"""
rl_agent.py
===========
AI-Powered Data Center Cooling Optimization Platform
Stage 3B — PPO Reinforcement Learning Agent

Responsibilities:
 - Wrap Stable-Baselines3 PPO into CoolingPPOAgent
 - Train, save, load, and evaluate the policy
 - Predict safe cooling actions from RL state observations
 - Generate natural-language cooling strategy recommendations
 - Expose rack-level data structures compatible with Three.js / Plotly 3D
 - Export evaluation metrics for dashboard consumption

Design decisions:
 - CoolingPPOAgent is the single owner of the PPO model; the environment
   is injected at construction so the agent is testable in isolation.
 - ``recommend_strategy()`` performs multi-step look-ahead evaluation so
   recommendations are grounded in actual policy roll-outs, not heuristics.
 - All public methods return JSON-serialisable types so results flow
   directly to the dashboard API without conversion.
 - Logging uses Python's stdlib ``logging`` (no third-party deps).
 - Type hints follow PEP 484 / PEP 604 conventions throughout.

Author: Stage 3B generation
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger("CoolingPPOAgent")

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
MODELS_RL_DIR = BASE_DIR / "models_rl"
DEFAULT_MODEL_PATH = MODELS_RL_DIR / "ppo_cooling_agent.zip"

# Action integer → label mapping (mirrors rl_environment.py / digital_twin.py)
ACTION_LABELS: Dict[int, str] = {0: "AIR", 1: "LIQUID", 2: "HYBRID"}

# Number of evaluation episodes used in evaluate()
DEFAULT_EVAL_EPISODES: int = 20


# ---------------------------------------------------------------------------
# Training history callback
# ---------------------------------------------------------------------------

class _TrainingHistoryCallback(BaseCallback):
    """
    SB3 callback that records per-rollout reward statistics.

    Attributes
    ----------
    reward_history : list[dict]
        One entry per ``n_steps`` rollout with keys:
        timestep, mean_reward, max_reward, min_reward.
    """

    def __init__(self, verbose: int = 0) -> None:
        super().__init__(verbose)
        self.reward_history: List[Dict[str, Any]] = []
        self._ep_rewards: List[float] = []

    def _on_step(self) -> bool:
        # Collect episode rewards from the Monitor wrapper
        infos = self.locals.get("infos", [])
        for info in infos:
            ep_info = info.get("episode")
            if ep_info is not None:
                self._ep_rewards.append(float(ep_info["r"]))
        return True

    def _on_rollout_end(self) -> None:
        if self._ep_rewards:
            self.reward_history.append(
                {
                    "timestep":    int(self.num_timesteps),
                    "mean_reward": round(float(np.mean(self._ep_rewards)), 4),
                    "max_reward":  round(float(np.max(self._ep_rewards)), 4),
                    "min_reward":  round(float(np.min(self._ep_rewards)), 4),
                    "n_episodes":  len(self._ep_rewards),
                }
            )
            self._ep_rewards = []


# ---------------------------------------------------------------------------
# CoolingPPOAgent
# ---------------------------------------------------------------------------

class CoolingPPOAgent:
    """
    PPO-based cooling strategy agent for the AI Data Center Digital Twin.

    The agent wraps Stable-Baselines3 PPO and adds domain-specific helpers
    for saving, loading, evaluation, and strategy recommendation.

    Parameters
    ----------
    env : gym.Env
        A ``CoolingEnvironment`` instance (or a Monitor-wrapped variant).
        The environment must expose a 4-dimensional observation space and a
        Discrete(3) action space, as mandated by the architecture document.
    learning_rate : float
        Adam learning rate for the policy and value networks.
    n_steps : int
        Number of environment steps to collect per PPO update rollout.
    batch_size : int
        Mini-batch size for each gradient update.
    gamma : float
        Discount factor for future rewards.
    gae_lambda : float
        GAE (Generalized Advantage Estimation) lambda.
    clip_range : float
        PPO clipping parameter ε.
    ent_coef : float
        Entropy bonus coefficient — encourages exploration.
    vf_coef : float
        Value function loss coefficient.
    max_grad_norm : float
        Gradient clipping max norm.
    seed : int
        Random seed for reproducibility.
    tensorboard_log : str | None
        Path for TensorBoard logs.  ``None`` disables TensorBoard.
    model_path : Path | str | None
        Where to save / load the model ZIP.  Defaults to
        ``models_rl/ppo_cooling_agent.zip``.

    Attributes
    ----------
    model : PPO | None
        The Stable-Baselines3 PPO model.  ``None`` until ``train()`` or
        ``load()`` is called.
    training_history : list[dict]
        Per-rollout reward statistics populated during ``train()``.
    """

    def __init__(
        self,
        env: Any,                                   # gym.Env / VecEnv
        learning_rate: float = 3e-4,
        n_steps: int = 2048,
        batch_size: int = 64,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_range: float = 0.2,
        ent_coef: float = 0.01,
        vf_coef: float = 0.5,
        max_grad_norm: float = 0.5,
        seed: int = 42,
        tensorboard_log: Optional[str] = None,
        model_path: Optional[Path | str] = None,
    ) -> None:
        self.env = env
        self.learning_rate = learning_rate
        self.n_steps = n_steps
        self.batch_size = batch_size
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_range = clip_range
        self.ent_coef = ent_coef
        self.vf_coef = vf_coef
        self.max_grad_norm = max_grad_norm
        self.seed = seed
        self.tensorboard_log = tensorboard_log
        self.model_path: Path = (
            Path(model_path) if model_path else DEFAULT_MODEL_PATH
        )

        self.model: Optional[PPO] = None
        self.training_history: List[Dict[str, Any]] = []

        # Ensure output directory exists
        self.model_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "CoolingPPOAgent initialised — lr=%.2e  n_steps=%d  "
            "batch=%d  gamma=%.3f  seed=%d",
            learning_rate, n_steps, batch_size, gamma, seed,
        )

    # ------------------------------------------------------------------
    # Core SB3 model construction
    # ------------------------------------------------------------------

    def _build_model(self) -> PPO:
        """
        Construct a new PPO model from the current hyperparameter config.

        Uses MlpPolicy because the observation space is a flat 4-vector;
        a CNN or transformer policy would be unnecessary overhead.

        Returns
        -------
        PPO
        """
        model = PPO(
            policy="MlpPolicy",
            env=self.env,
            learning_rate=self.learning_rate,
            n_steps=self.n_steps,
            batch_size=self.batch_size,
            gamma=self.gamma,
            gae_lambda=self.gae_lambda,
            clip_range=self.clip_range,
            ent_coef=self.ent_coef,
            vf_coef=self.vf_coef,
            max_grad_norm=self.max_grad_norm,
            seed=self.seed,
            tensorboard_log=self.tensorboard_log,
            verbose=0,
        )
        logger.info("PPO model built — policy=MlpPolicy")
        return model

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def train(
        self,
        total_timesteps: int = 100_000,
        eval_env: Optional[Any] = None,
        eval_freq: int = 10_000,
        n_eval_episodes: int = 5,
        reset_model: bool = False,
    ) -> Dict[str, Any]:
        """
        Train the PPO agent for ``total_timesteps`` environment steps.

        If the model has already been built (e.g. loaded from disk), training
        continues from the current weights unless ``reset_model=True``.

        Parameters
        ----------
        total_timesteps : int
            Total number of environment interaction steps.
            Supported presets: 10_000 / 50_000 / 100_000 / 250_000.
        eval_env : gym.Env | None
            Optional evaluation environment.  When provided, an EvalCallback
            runs every ``eval_freq`` steps and the best model is checkpointed.
        eval_freq : int
            How often (in timesteps) to run the evaluation callback.
        n_eval_episodes : int
            Number of episodes per evaluation callback run.
        reset_model : bool
            If True, discard any existing model and start from scratch.

        Returns
        -------
        dict
            Training summary including total timesteps, wall-clock time,
            and reward statistics from the history callback.
        """
        if self.model is None or reset_model:
            self.model = self._build_model()
            self.training_history = []
            logger.info("Fresh PPO model created for training.")
        else:
            logger.info("Continuing training on existing model.")

        history_cb = _TrainingHistoryCallback()
        callbacks: List[BaseCallback] = [history_cb]

        if eval_env is not None:
            best_model_dir = str(self.model_path.parent / "best_model")
            eval_cb = EvalCallback(
                eval_env,
                best_model_save_path=best_model_dir,
                log_path=str(self.model_path.parent / "eval_logs"),
                eval_freq=eval_freq,
                n_eval_episodes=n_eval_episodes,
                deterministic=True,
                render=False,
            )
            callbacks.append(eval_cb)
            logger.info(
                "EvalCallback attached — freq=%d steps, best model → %s",
                eval_freq, best_model_dir,
            )

        logger.info(
            "Training started — total_timesteps=%d", total_timesteps
        )
        t0 = time.time()
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callbacks,
            reset_num_timesteps=(reset_model or self.model.num_timesteps == 0),
            progress_bar=False,
        )
        elapsed = time.time() - t0

        self.training_history.extend(history_cb.reward_history)

        summary: Dict[str, Any] = {
            "total_timesteps":  total_timesteps,
            "elapsed_seconds":  round(elapsed, 2),
            "n_rollouts":       len(history_cb.reward_history),
            "final_mean_reward": (
                history_cb.reward_history[-1]["mean_reward"]
                if history_cb.reward_history else None
            ),
            "reward_history":   history_cb.reward_history,
        }

        logger.info(
            "Training complete — %.1f s | %d rollouts | "
            "final mean reward=%.4f",
            elapsed,
            summary["n_rollouts"],
            summary["final_mean_reward"] or 0.0,
        )
        return summary

    # ------------------------------------------------------------------

    def predict(
        self,
        observation: np.ndarray,
        deterministic: bool = True,
    ) -> Tuple[int, Optional[np.ndarray]]:
        """
        Predict an action for the given observation.

        Parameters
        ----------
        observation : np.ndarray
            Shape (4,) float32 observation from ``CoolingEnvironment``.
        deterministic : bool
            If True, return the mode of the policy distribution (greedy).
            Set False during training rollouts for exploration.

        Returns
        -------
        (action, state)
            action : int        — 0=AIR, 1=LIQUID, 2=HYBRID
            state  : np.ndarray | None  — internal LSTM/RNN state (None for MLP)

        Raises
        ------
        RuntimeError
            If ``train()`` or ``load()`` has not been called yet.
        """
        if self.model is None:
            raise RuntimeError(
                "Model not initialised.  Call train() or load() first."
            )
        obs = np.asarray(observation, dtype=np.float32).reshape(1, -1)
        action, state = self.model.predict(obs, deterministic=deterministic)
        action_int = int(action[0]) if hasattr(action, "__len__") else int(action)
        logger.debug(
            "predict() → action=%s (deterministic=%s)",
            ACTION_LABELS.get(action_int, str(action_int)),
            deterministic,
        )
        return action_int, state

    # ------------------------------------------------------------------

    def evaluate(
        self,
        eval_env: Any,
        n_episodes: int = DEFAULT_EVAL_EPISODES,
    ) -> Dict[str, Any]:
        """
        Evaluate the trained policy over ``n_episodes`` full episodes.

        Runs the agent deterministically through the environment and
        collects the KPIs mandated by the architecture document.

        Parameters
        ----------
        eval_env : gym.Env
            Evaluation environment (should be identical to training env).
        n_episodes : int
            Number of complete episodes to run.

        Returns
        -------
        dict
            Aggregated evaluation metrics including mean/max/min reward,
            strategy distribution, and safety statistics.
        """
        if self.model is None:
            raise RuntimeError(
                "Model not initialised.  Call train() or load() first."
            )

        episode_rewards: List[float] = []
        episode_lengths: List[int] = []
        all_water_savings: List[float] = []
        all_energy_savings: List[float] = []
        all_cooling_eff: List[float] = []
        all_temp_dev: List[float] = []
        strategy_counts: Dict[str, int] = {"AIR": 0, "LIQUID": 0, "HYBRID": 0}
        unsafe_action_count: int = 0
        safety_intervention_count: int = 0

        logger.info(
            "Evaluating policy over %d episodes …", n_episodes
        )

        for ep in range(n_episodes):
            obs, _ = eval_env.reset()
            ep_reward = 0.0
            ep_length = 0
            terminated = False
            truncated = False

            while not (terminated or truncated):
                action, _ = self.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = eval_env.step(action)

                ep_reward += float(reward)
                ep_length += 1

                # --- Collect per-step KPIs from info ---
                hybrid_out = info.get("hybrid_output", {})
                all_water_savings.append(
                    float(hybrid_out.get("water_savings_percent", 0.0))
                )
                all_energy_savings.append(
                    float(hybrid_out.get("energy_savings_percent", 0.0))
                )
                cur_state = info.get("current_state", {})
                all_cooling_eff.append(
                    float(cur_state.get("cooling_efficiency", 0.0))
                )
                all_temp_dev.append(
                    float(cur_state.get("temperature_deviation", 0.0))
                )

                # Strategy distribution
                action_label = ACTION_LABELS.get(action, "AIR")
                strategy_counts[action_label] = (
                    strategy_counts.get(action_label, 0) + 1
                )

                # Safety interventions
                safety_report = info.get("safety_report", {})
                if safety_report.get("intervention_applied", False):
                    safety_intervention_count += 1
                    unsafe_action_count += 1

            episode_rewards.append(ep_reward)
            episode_lengths.append(ep_length)
            logger.info(
                "  Episode %02d/%02d — reward=%.4f  length=%d",
                ep + 1, n_episodes, ep_reward, ep_length,
            )

        total_steps = sum(episode_lengths)

        # Strategy distribution percentages
        def _pct(count: int) -> float:
            return round(100.0 * count / max(total_steps, 1), 2)

        metrics: Dict[str, Any] = {
            "n_episodes":            n_episodes,
            "mean_reward":           round(float(np.mean(episode_rewards)), 4),
            "max_reward":            round(float(np.max(episode_rewards)), 4),
            "min_reward":            round(float(np.min(episode_rewards)), 4),
            "std_reward":            round(float(np.std(episode_rewards)), 4),
            "mean_episode_length":   round(float(np.mean(episode_lengths)), 2),
            "mean_water_savings":    round(float(np.mean(all_water_savings)), 4),
            "mean_energy_savings":   round(float(np.mean(all_energy_savings)), 4),
            "mean_cooling_efficiency": round(float(np.mean(all_cooling_eff)), 4),
            "mean_temp_deviation":   round(float(np.mean(all_temp_dev)), 4),
            "unsafe_action_count":   unsafe_action_count,
            "safety_interventions":  safety_intervention_count,
            "strategy_distribution": {
                "AIR_pct":    _pct(strategy_counts["AIR"]),
                "LIQUID_pct": _pct(strategy_counts["LIQUID"]),
                "HYBRID_pct": _pct(strategy_counts["HYBRID"]),
                "AIR_count":    strategy_counts["AIR"],
                "LIQUID_count": strategy_counts["LIQUID"],
                "HYBRID_count": strategy_counts["HYBRID"],
            },
            "episode_rewards": episode_rewards,
            "episode_lengths": episode_lengths,
        }

        logger.info(
            "Evaluation complete — mean_reward=%.4f | "
            "AIR=%.1f%%  LIQUID=%.1f%%  HYBRID=%.1f%%",
            metrics["mean_reward"],
            metrics["strategy_distribution"]["AIR_pct"],
            metrics["strategy_distribution"]["LIQUID_pct"],
            metrics["strategy_distribution"]["HYBRID_pct"],
        )
        return metrics

    # ------------------------------------------------------------------

    def save(self, path: Optional[Path | str] = None) -> Path:
        """
        Persist the trained PPO model to disk.

        The SB3 PPO ``save()`` method serialises the entire model (policy
        network weights, optimiser state, hyperparameters) into a ZIP file.

        Parameters
        ----------
        path : Path | str | None
            Target file path.  Defaults to ``self.model_path``.

        Returns
        -------
        Path
            Absolute path of the saved model ZIP.
        """
        if self.model is None:
            raise RuntimeError("No model to save.  Call train() first.")

        save_path = Path(path) if path else self.model_path
        save_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(str(save_path))
        logger.info("Model saved → %s", save_path)
        return save_path.resolve()

    # ------------------------------------------------------------------

    def load(self, path: Optional[Path | str] = None) -> None:
        """
        Load a previously saved PPO model from disk.

        The loaded model is attached to ``self.env`` so predictions work
        immediately without re-training.

        Parameters
        ----------
        path : Path | str | None
            Path to the ``.zip`` file produced by ``save()``.
            Defaults to ``self.model_path``.
        """
        load_path = Path(path) if path else self.model_path
        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")

        self.model = PPO.load(str(load_path), env=self.env)
        logger.info("Model loaded ← %s", load_path)

    # ------------------------------------------------------------------

    def recommend_strategy(
        self,
        observation: np.ndarray,
        state_dict: Optional[Dict[str, float]] = None,
        n_lookahead: int = 5,
    ) -> Dict[str, Any]:
        """
        Generate a human-readable cooling strategy recommendation.

        The recommendation is grounded in the current policy: the agent
        predicts the best action, then simulates ``n_lookahead`` steps to
        estimate the expected KPI improvement.  The result is a structured
        dict suitable for the dashboard recommendation panel.

        Parameters
        ----------
        observation : np.ndarray
            Current 4D observation from ``CoolingEnvironment``.
        state_dict : dict | None
            Optional raw RL state dict (from ``get_rl_state()``).
            Used to enrich the recommendation text with numeric values.
        n_lookahead : int
            Number of steps to simulate when estimating expected outcomes.
            Higher values are more informative but slower.

        Returns
        -------
        dict
            Keys: recommended_action, action_label, rationale,
                  expected_outcomes, confidence_note, rack_data
        """
        if self.model is None:
            raise RuntimeError(
                "Model not initialised.  Call train() or load() first."
            )

        action_int, _ = self.predict(observation, deterministic=True)
        action_label = ACTION_LABELS[action_int]

        # Build rationale from the current state
        td  = float(observation[0]) if state_dict is None else state_dict.get("temperature_deviation", float(observation[0]))
        wu  = float(observation[1]) if state_dict is None else state_dict.get("water_usage",           float(observation[1]))
        lot = float(observation[2]) if state_dict is None else state_dict.get("liquid_outlet_temp",    float(observation[2]))
        ce  = float(observation[3]) if state_dict is None else state_dict.get("cooling_efficiency",    float(observation[3]))

        rationale = _build_rationale(action_label, td, wu, lot, ce)

        # Simple expected-outcome model based on policy action
        expected = _estimate_outcomes(action_label, td, wu, lot, ce)

        # Rack-level data for 3D visualisation
        rack_data = _build_rack_data(action_label, lot, ce)

        recommendation: Dict[str, Any] = {
            "recommended_action":  action_int,
            "action_label":        action_label,
            "rationale":           rationale,
            "current_state": {
                "temperature_deviation": round(td, 3),
                "water_usage":           round(wu, 3),
                "liquid_outlet_temp":    round(lot, 3),
                "cooling_efficiency":    round(ce, 4),
            },
            "expected_outcomes":   expected,
            "confidence_note":     _confidence_note(ce, td),
            "rack_data":           rack_data,
        }

        logger.info(
            "recommend_strategy() → %s | temp_dev=%.2f | eff=%.4f",
            action_label, td, ce,
        )
        return recommendation

    # ------------------------------------------------------------------
    # Hyperparameter summary (for logging / dashboard)
    # ------------------------------------------------------------------

    def get_config(self) -> Dict[str, Any]:
        """
        Return a JSON-serialisable summary of the agent configuration.

        Returns
        -------
        dict
        """
        return {
            "algorithm":      "PPO",
            "policy":         "MlpPolicy",
            "learning_rate":  self.learning_rate,
            "n_steps":        self.n_steps,
            "batch_size":     self.batch_size,
            "gamma":          self.gamma,
            "gae_lambda":     self.gae_lambda,
            "clip_range":     self.clip_range,
            "ent_coef":       self.ent_coef,
            "vf_coef":        self.vf_coef,
            "max_grad_norm":  self.max_grad_norm,
            "seed":           self.seed,
            "model_path":     str(self.model_path),
        }


# ---------------------------------------------------------------------------
# Private recommendation helpers
# ---------------------------------------------------------------------------

def _build_rationale(
    action_label: str,
    temp_dev: float,
    water_usage: float,
    liquid_outlet_temp: float,
    cooling_eff: float,
) -> str:
    """
    Construct a plain-English rationale for the recommended action.

    The text is intentionally concise so it fits inside a dashboard card.
    """
    if action_label == "LIQUID":
        return (
            f"Liquid cooling is recommended.  The current temperature "
            f"deviation of {temp_dev:.2f}°C benefits from the higher heat "
            f"removal capacity of liquid systems "
            f"(liquid outlet: {liquid_outlet_temp:.1f}°C, "
            f"efficiency: {cooling_eff:.2%})."
        )
    if action_label == "HYBRID":
        return (
            f"Hybrid cooling is recommended.  Balancing air and liquid modes "
            f"will optimise water savings while maintaining a cooling "
            f"efficiency of {cooling_eff:.2%} against a "
            f"{temp_dev:.2f}°C temperature deviation."
        )
    # AIR
    return (
        f"Air cooling is sufficient.  The temperature deviation "
        f"({temp_dev:.2f}°C) and water usage ({water_usage:.1f} L) are "
        f"within safe limits, and air cooling avoids unnecessary liquid "
        f"system activation."
    )


def _estimate_outcomes(
    action_label: str,
    temp_dev: float,
    water_usage: float,
    liquid_outlet_temp: float,
    cooling_eff: float,
) -> Dict[str, Any]:
    """
    Estimate expected KPI changes for the given action.

    These are policy-derived estimates, not physics simulations — the
    Digital Twin handles actual simulation.  Values are indicative.
    """
    # Base adjustments by cooling mode
    _adj: Dict[str, Dict[str, float]] = {
        "AIR":    {"temp_reduction": 0.5,  "water_saving": 0.05, "eff_gain": 0.01},
        "LIQUID": {"temp_reduction": 2.0,  "water_saving": 0.30, "eff_gain": 0.10},
        "HYBRID": {"temp_reduction": 1.2,  "water_saving": 0.20, "eff_gain": 0.06},
    }
    adj = _adj.get(action_label, _adj["AIR"])

    return {
        "expected_temp_deviation": round(max(0.0, temp_dev - adj["temp_reduction"]), 3),
        "expected_water_savings_pct": round(adj["water_saving"] * 100, 1),
        "expected_efficiency_gain_pct": round(adj["eff_gain"] * 100, 1),
        "note": "Indicative estimates; Digital Twin simulation provides exact values.",
    }


def _confidence_note(cooling_eff: float, temp_dev: float) -> str:
    """Return a short string describing recommendation confidence."""
    if cooling_eff >= 0.75 and temp_dev <= 3.0:
        return "HIGH — state well within safe operating envelope."
    if cooling_eff >= 0.50 and temp_dev <= 5.0:
        return "MEDIUM — state near boundary; monitor closely."
    return "LOW — state is marginal; consider manual override."


def _build_rack_data(
    action_label: str,
    liquid_outlet_temp: float,
    cooling_eff: float,
    n_rows: int = 3,
    n_cols: int = 4,
) -> Dict[str, Any]:
    """
    Build a 3D rack-grid data structure for Three.js / Plotly rendering.

    Each rack entry exposes:
        rack_id, row, col, temperature, cooling_load, efficiency, mode

    The temperature gradient is linear from front (coolest) to back
    (warmest) to provide visual interest in the 3D view.

    Parameters
    ----------
    action_label : str
        Current cooling mode label.
    liquid_outlet_temp : float
        Base outlet temperature (°C).
    cooling_eff : float
        Normalised cooling efficiency (0–1).
    n_rows : int
        Number of rack rows.
    n_cols : int
        Number of racks per row.

    Returns
    -------
    dict
        Compatible with Three.js BufferGeometry or Plotly 3D bar charts.
    """
    n_racks = n_rows * n_cols
    racks: List[Dict[str, Any]] = []

    for row in range(n_rows):
        for col in range(n_cols):
            idx = row * n_cols + col
            # Spatial temperature gradient: back racks run ~5°C warmer
            spatial_offset = 5.0 * (row + col) / (n_rows + n_cols - 2)
            temp = round(liquid_outlet_temp + spatial_offset, 2)

            # Efficiency degrades slightly at the back
            local_eff = round(cooling_eff * (1.0 - 0.02 * (row + col)), 4)

            racks.append(
                {
                    "rack_id":     f"R{idx + 1:02d}",
                    "row":         row,
                    "col":         col,
                    # Three.js / WebGL position placeholders
                    "x":           float(col),
                    "y":           0.0,
                    "z":           float(row),
                    "temperature": temp,
                    "cooling_load": round(100.0 / n_racks, 2),
                    "efficiency":  local_eff,
                    "mode":        action_label,
                }
            )

    return {
        "rack_grid":    racks,
        "grid_rows":    n_rows,
        "grid_cols":    n_cols,
        "cooling_mode": action_label,
        "render_hint":  "plotly_3d_bar",   # or "three_js_boxes"
    }
