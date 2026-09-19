"""
train_rl.py
===========
AI-Powered Data Center Cooling Optimization Platform
Stage 3B — Reinforcement Learning Training Pipeline

Responsibilities:
 - Create environment, safety filter, and PPO agent
 - Train the agent for a configurable number of timesteps
 - Evaluate the trained policy
 - Save the model and all training artefacts
 - Export dashboard-ready CSV / JSON files

Pipeline
--------
    env
    ↓
    safety filter (injected into env)
    ↓
    PPO training  (model.learn())
    ↓
    evaluation    (n_episodes deterministic roll-outs)
    ↓
    model save    (models_rl/ppo_cooling_agent.zip)
    ↓
    dashboard export  (dashboard_exports/*.csv)

Output directories
------------------
    models_rl/
        ppo_cooling_agent.zip
        training_metrics.json
        evaluation_metrics.json
        training_history.csv

    dashboard_exports/
        reward_history.csv
        strategy_history.csv
        safety_history.csv
        episode_summary.csv

Design decisions:
 - ``main()`` is the single entry point; ``train()``, ``evaluate()``, and
   ``save_results()`` are separated for testability and re-use.
 - The training and evaluation environments share the same base parameters
   but are constructed independently to avoid state leakage.
 - Monitor wrapper applied to both envs so SB3 can track episode statistics
   (required by the training history callback).
 - All numeric data written as CSVs so the dashboard can consume them with
   Pandas / JavaScript without a database.
 - Timestep presets are validated at startup; invalid values raise a
   descriptive error rather than silently defaulting.

Author: Stage 3B generation
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from stable_baselines3.common.monitor import Monitor

# Project imports
from digital_twin import get_rl_state          # Digital Twin RL hook
from rl_environment import CoolingEnvironment   # Stage 3A environment
from safety_filter import SafetyFilter          # Stage 3A safety layer
from rl_agent import CoolingPPOAgent            # Stage 3B agent (this stage)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger("TrainRL")

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
MODELS_RL_DIR    = BASE_DIR / "models_rl"
DASHBOARD_DIR    = BASE_DIR / "dashboard_exports"

# ---------------------------------------------------------------------------
# Supported timestep presets (validated in main)
# ---------------------------------------------------------------------------
TIMESTEP_PRESETS = (
    10_000,
    50_000,
    100_000,
    250_000,
)

DEFAULT_TIMESTEPS = 50_000

# ---------------------------------------------------------------------------
# Default Digital Twin input parameters
# These represent a typical warm-day, medium-workload operating point.
# Override via CLI flags or programmatic calls to train() / main().
# ---------------------------------------------------------------------------
DEFAULT_AIR_PARAMS: Dict[str, Any] = {
    "Server_Workload":                  75.0,
    "Inlet_Temperature":                24.0,
    "Ambient_Temperature":              30.0,
    "Chiller_Usage":                    65.0,
    "AHU_Usage":                        40.0,
    "Cooling_Strategy_Encoded":         2,
    "Cooling_Unit_Power_Consumption_kW": 12.5,
}

DEFAULT_LIQUID_PARAMS: Dict[str, Any] = {
    "avg_P_ac":    6.0,
    "avg_P_cu":    3.5,
    "avg_T_out":   26.0,
    "avg_T_MEAS":  29.0,
    "avg_T_celCC": 32.0,
    "TLHC":        55.0,
    "DoW":         3.0,
    "WeH":         0.0,
}


# ---------------------------------------------------------------------------
# Environment factory
# ---------------------------------------------------------------------------

def _make_env(
    air_params: Dict[str, Any],
    liquid_params: Dict[str, Any],
    max_steps: int,
    safety_filter: SafetyFilter,
    monitor_log_dir: Optional[Path] = None,
) -> Monitor:
    """
    Build a monitored ``CoolingEnvironment``.

    The Monitor wrapper records per-episode reward / length statistics which
    are consumed by the SB3 training callbacks and the training history.

    Parameters
    ----------
    air_params, liquid_params : dict
        Digital Twin input parameters (see digital_twin.py).
    max_steps : int
        Maximum steps per episode.
    safety_filter : SafetyFilter
        Shared safety filter instance.
    monitor_log_dir : Path | None
        Directory for Monitor CSV logs.  ``None`` disables file logging.

    Returns
    -------
    Monitor
    """
    env = CoolingEnvironment(
        air_params=air_params,
        liquid_params=liquid_params,
        max_steps=max_steps,
        safety_filter=safety_filter,
    )
    log_dir: Optional[str] = str(monitor_log_dir) if monitor_log_dir else None
    if log_dir:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
    return Monitor(env, filename=log_dir)


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

def train(
    total_timesteps: int = DEFAULT_TIMESTEPS,
    air_params: Optional[Dict[str, Any]] = None,
    liquid_params: Optional[Dict[str, Any]] = None,
    max_steps_per_episode: int = 100,
    eval_freq: int = 10_000,
    n_eval_episodes: int = 5,
    agent_kwargs: Optional[Dict[str, Any]] = None,
) -> Tuple[CoolingPPOAgent, Dict[str, Any]]:
    """
    Create all components and run the PPO training loop.

    Parameters
    ----------
    total_timesteps : int
        Total environment interaction steps.
    air_params : dict | None
        Digital Twin air parameters.  Defaults to ``DEFAULT_AIR_PARAMS``.
    liquid_params : dict | None
        Digital Twin liquid parameters.  Defaults to ``DEFAULT_LIQUID_PARAMS``.
    max_steps_per_episode : int
        Steps per episode before truncation.
    eval_freq : int
        Evaluation callback frequency (timesteps).
    n_eval_episodes : int
        Episodes per evaluation callback.
    agent_kwargs : dict | None
        Override any ``CoolingPPOAgent`` constructor keyword arguments.

    Returns
    -------
    (agent, training_summary)
    """
    air_params    = air_params    or DEFAULT_AIR_PARAMS
    liquid_params = liquid_params or DEFAULT_LIQUID_PARAMS
    agent_kwargs  = agent_kwargs  or {}

    logger.info("=== Stage 3B — PPO Training ===")
    logger.info("  timesteps=%d  max_steps/ep=%d", total_timesteps, max_steps_per_episode)

    # ---- Safety filter (shared across train + eval envs) ----
    safety_filter = SafetyFilter()

    # ---- Training environment ----
    train_env = _make_env(
        air_params=air_params,
        liquid_params=liquid_params,
        max_steps=max_steps_per_episode,
        safety_filter=safety_filter,
        monitor_log_dir=MODELS_RL_DIR / "monitor_train",
    )

    # ---- Evaluation environment ----
    eval_env = _make_env(
        air_params=air_params,
        liquid_params=liquid_params,
        max_steps=max_steps_per_episode,
        safety_filter=safety_filter,
        monitor_log_dir=MODELS_RL_DIR / "monitor_eval",
    )

    # ---- Agent ----
    agent = CoolingPPOAgent(
        env=train_env,
        model_path=MODELS_RL_DIR / "ppo_cooling_agent.zip",
        **agent_kwargs,
    )

    logger.info("Agent config: %s", json.dumps(agent.get_config(), indent=2))

    # ---- Train ----
    training_summary = agent.train(
        total_timesteps=total_timesteps,
        eval_env=eval_env,
        eval_freq=eval_freq,
        n_eval_episodes=n_eval_episodes,
        reset_model=True,
    )

    train_env.close()
    eval_env.close()

    logger.info(
        "Training summary — elapsed=%.1fs | mean_reward=%.4f",
        training_summary["elapsed_seconds"],
        training_summary["final_mean_reward"] or 0.0,
    )
    return agent, training_summary


# ---------------------------------------------------------------------------
# Evaluate
# ---------------------------------------------------------------------------

def evaluate(
    agent: CoolingPPOAgent,
    air_params: Optional[Dict[str, Any]] = None,
    liquid_params: Optional[Dict[str, Any]] = None,
    max_steps_per_episode: int = 100,
    n_episodes: int = 20,
) -> Dict[str, Any]:
    """
    Evaluate a trained agent and collect dashboard KPIs.

    Parameters
    ----------
    agent : CoolingPPOAgent
        A trained (or loaded) agent.
    air_params, liquid_params : dict | None
        Digital Twin parameters.  Defaults to the project defaults.
    max_steps_per_episode : int
        Steps per episode.
    n_episodes : int
        Number of evaluation episodes.

    Returns
    -------
    dict
        Full evaluation metrics dict (see ``CoolingPPOAgent.evaluate()``).
    """
    air_params    = air_params    or DEFAULT_AIR_PARAMS
    liquid_params = liquid_params or DEFAULT_LIQUID_PARAMS

    safety_filter = SafetyFilter()
    eval_env = _make_env(
        air_params=air_params,
        liquid_params=liquid_params,
        max_steps=max_steps_per_episode,
        safety_filter=safety_filter,
    )

    logger.info("=== Evaluation — %d episodes ===", n_episodes)
    metrics = agent.evaluate(eval_env, n_episodes=n_episodes)
    eval_env.close()
    return metrics


# ---------------------------------------------------------------------------
# Save results
# ---------------------------------------------------------------------------

def save_results(
    agent: CoolingPPOAgent,
    training_summary: Dict[str, Any],
    evaluation_metrics: Dict[str, Any],
) -> Dict[str, Path]:
    """
    Persist all artefacts required by the architecture document.

    Writes to:
        models_rl/
            ppo_cooling_agent.zip
            training_metrics.json
            evaluation_metrics.json
            training_history.csv

        dashboard_exports/
            reward_history.csv
            strategy_history.csv
            safety_history.csv
            episode_summary.csv

    Parameters
    ----------
    agent : CoolingPPOAgent
        Trained agent with populated ``training_history``.
    training_summary : dict
        Output of ``train()``.
    evaluation_metrics : dict
        Output of ``evaluate()``.

    Returns
    -------
    dict
        Mapping from artefact name → absolute Path.
    """
    MODELS_RL_DIR.mkdir(parents=True, exist_ok=True)
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    saved: Dict[str, Path] = {}

    # ---- 1. PPO model ZIP ----
    model_zip = agent.save()
    saved["model_zip"] = model_zip
    logger.info("Saved model ZIP → %s", model_zip)

    # ---- 2. Training metrics JSON ----
    train_meta = {
        "generated_at":     _utc_now(),
        "agent_config":     agent.get_config(),
        "training_summary": {
            k: v for k, v in training_summary.items()
            if k != "reward_history"  # large; stored separately in CSV
        },
    }
    tm_path = MODELS_RL_DIR / "training_metrics.json"
    _write_json(tm_path, train_meta)
    saved["training_metrics"] = tm_path

    # ---- 3. Evaluation metrics JSON ----
    eval_meta = {
        "generated_at":       _utc_now(),
        "evaluation_metrics": {
            k: v for k, v in evaluation_metrics.items()
            if k not in ("episode_rewards", "episode_lengths")
        },
    }
    em_path = MODELS_RL_DIR / "evaluation_metrics.json"
    _write_json(em_path, eval_meta)
    saved["evaluation_metrics"] = em_path

    # ---- 4. Training history CSV ----
    th_path = MODELS_RL_DIR / "training_history.csv"
    _write_csv(
        th_path,
        rows=training_summary.get("reward_history", []),
        fieldnames=["timestep", "mean_reward", "max_reward", "min_reward", "n_episodes"],
    )
    saved["training_history_csv"] = th_path

    # ---- 5. reward_history.csv (dashboard) ----
    rh_path = DASHBOARD_DIR / "reward_history.csv"
    _write_csv(
        rh_path,
        rows=training_summary.get("reward_history", []),
        fieldnames=["timestep", "mean_reward", "max_reward", "min_reward"],
    )
    saved["reward_history_csv"] = rh_path

    # ---- 6. strategy_history.csv (dashboard) ----
    strat_dist = evaluation_metrics.get("strategy_distribution", {})
    strategy_rows = [
        {
            "strategy": "AIR",
            "count":    strat_dist.get("AIR_count", 0),
            "pct":      strat_dist.get("AIR_pct", 0.0),
        },
        {
            "strategy": "LIQUID",
            "count":    strat_dist.get("LIQUID_count", 0),
            "pct":      strat_dist.get("LIQUID_pct", 0.0),
        },
        {
            "strategy": "HYBRID",
            "count":    strat_dist.get("HYBRID_count", 0),
            "pct":      strat_dist.get("HYBRID_pct", 0.0),
        },
    ]
    sh_path = DASHBOARD_DIR / "strategy_history.csv"
    _write_csv(sh_path, rows=strategy_rows, fieldnames=["strategy", "count", "pct"])
    saved["strategy_history_csv"] = sh_path

    # ---- 7. safety_history.csv (dashboard) ----
    safety_rows = [
        {
            "metric":          "safety_interventions",
            "value":           evaluation_metrics.get("safety_interventions", 0),
        },
        {
            "metric":          "unsafe_action_count",
            "value":           evaluation_metrics.get("unsafe_action_count", 0),
        },
        {
            "metric":          "n_episodes",
            "value":           evaluation_metrics.get("n_episodes", 0),
        },
    ]
    safeh_path = DASHBOARD_DIR / "safety_history.csv"
    _write_csv(safeh_path, rows=safety_rows, fieldnames=["metric", "value"])
    saved["safety_history_csv"] = safeh_path

    # ---- 8. episode_summary.csv (dashboard) ----
    ep_rewards  = evaluation_metrics.get("episode_rewards", [])
    ep_lengths  = evaluation_metrics.get("episode_lengths", [])
    ep_rows = [
        {
            "episode":        i + 1,
            "total_reward":   round(r, 4),
            "episode_length": l,
        }
        for i, (r, l) in enumerate(zip(ep_rewards, ep_lengths))
    ]
    eps_path = DASHBOARD_DIR / "episode_summary.csv"
    _write_csv(eps_path, rows=ep_rows, fieldnames=["episode", "total_reward", "episode_length"])
    saved["episode_summary_csv"] = eps_path

    logger.info("All artefacts saved:")
    for name, path in saved.items():
        logger.info("  %-30s → %s", name, path)

    return saved


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(
    total_timesteps: int = DEFAULT_TIMESTEPS,
    n_eval_episodes: int = 20,
    max_steps_per_episode: int = 100,
    agent_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Full end-to-end training pipeline.

    Sequence:
        1.  Validate timestep preset
        2.  Train PPO agent
        3.  Save trained model
        4.  Evaluate trained model
        5.  Save all artefacts and export dashboard CSVs
        6.  Print summary

    Parameters
    ----------
    total_timesteps : int
        Must be one of TIMESTEP_PRESETS (10_000 / 50_000 / 100_000 / 250_000).
    n_eval_episodes : int
        Number of evaluation episodes after training.
    max_steps_per_episode : int
        Maximum steps per episode for both train and eval envs.
    agent_kwargs : dict | None
        Optional overrides for ``CoolingPPOAgent`` hyperparameters.
        Example: {"learning_rate": 1e-4, "n_steps": 1024}

    Returns
    -------
    dict
        Pipeline result with keys: training_summary, evaluation_metrics,
        saved_artefacts, pipeline_elapsed_seconds.
    """
    # --- Validate timestep preset ---
    if total_timesteps not in TIMESTEP_PRESETS:
        raise ValueError(
            f"total_timesteps must be one of {TIMESTEP_PRESETS}; "
            f"got {total_timesteps}."
        )

    pipeline_start = time.time()

    logger.info(
        "╔══════════════════════════════════════════════════════╗"
    )
    logger.info(
        "║  Stage 3B — PPO Training Pipeline                   ║"
    )
    logger.info(
        "╚══════════════════════════════════════════════════════╝"
    )
    logger.info("  timesteps=%d  eval_episodes=%d", total_timesteps, n_eval_episodes)

    # --- Step 1 & 2: Train ---
    agent, training_summary = train(
        total_timesteps=total_timesteps,
        max_steps_per_episode=max_steps_per_episode,
        agent_kwargs=agent_kwargs,
    )

    # --- Step 3: Intermediate model save (in case eval fails) ---
    agent.save()

    # --- Step 4: Evaluate ---
    evaluation_metrics = evaluate(
        agent=agent,
        max_steps_per_episode=max_steps_per_episode,
        n_episodes=n_eval_episodes,
    )

    # --- Step 5: Save all artefacts ---
    saved_artefacts = save_results(agent, training_summary, evaluation_metrics)

    pipeline_elapsed = round(time.time() - pipeline_start, 2)

    # --- Step 6: Print summary ---
    _print_summary(training_summary, evaluation_metrics, pipeline_elapsed)

    return {
        "training_summary":      training_summary,
        "evaluation_metrics":    evaluation_metrics,
        "saved_artefacts":       {k: str(v) for k, v in saved_artefacts.items()},
        "pipeline_elapsed_seconds": pipeline_elapsed,
    }


# ---------------------------------------------------------------------------
# Private utilities
# ---------------------------------------------------------------------------

def _print_summary(
    training_summary: Dict[str, Any],
    evaluation_metrics: Dict[str, Any],
    elapsed: float,
) -> None:
    """Print a formatted pipeline summary to stdout and the log."""
    strat = evaluation_metrics.get("strategy_distribution", {})
    lines = [
        "",
        "═" * 58,
        "  Pipeline Complete",
        "═" * 58,
        f"  Training timesteps   : {training_summary.get('total_timesteps', '?'):,}",
        f"  Training time        : {training_summary.get('elapsed_seconds', 0):.1f} s",
        f"  Rollouts collected   : {training_summary.get('n_rollouts', '?')}",
        f"  Final mean reward    : {training_summary.get('final_mean_reward') or 0.0:.4f}",
        "  ─" * 29,
        f"  Eval episodes        : {evaluation_metrics.get('n_episodes', '?')}",
        f"  Mean reward          : {evaluation_metrics.get('mean_reward', 0.0):.4f}",
        f"  Max  reward          : {evaluation_metrics.get('max_reward', 0.0):.4f}",
        f"  Mean cooling eff     : {evaluation_metrics.get('mean_cooling_efficiency', 0.0):.4f}",
        f"  Mean temp deviation  : {evaluation_metrics.get('mean_temp_deviation', 0.0):.3f}°C",
        f"  Mean water savings   : {evaluation_metrics.get('mean_water_savings', 0.0):.2f}%",
        f"  Mean energy savings  : {evaluation_metrics.get('mean_energy_savings', 0.0):.2f}%",
        f"  Safety interventions : {evaluation_metrics.get('safety_interventions', 0)}",
        "  ─" * 29,
        f"  Strategy — AIR       : {strat.get('AIR_pct', 0.0):.1f}%",
        f"  Strategy — LIQUID    : {strat.get('LIQUID_pct', 0.0):.1f}%",
        f"  Strategy — HYBRID    : {strat.get('HYBRID_pct', 0.0):.1f}%",
        "  ─" * 29,
        f"  Total pipeline time  : {elapsed:.1f} s",
        "═" * 58,
    ]
    for line in lines:
        logger.info(line)
    print("\n".join(lines))


def _write_json(path: Path, data: Any) -> None:
    """Write JSON-serialisable ``data`` to ``path`` with 2-space indent."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    logger.debug("JSON written → %s", path)


def _write_csv(
    path: Path,
    rows: List[Dict[str, Any]],
    fieldnames: List[str],
) -> None:
    """Write ``rows`` (list of dicts) as a CSV with a header row."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    logger.debug("CSV written → %s (%d rows)", path, len(rows))


def _utc_now() -> str:
    """Return the current UTC timestamp as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the PPO cooling agent (Stage 3B).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=DEFAULT_TIMESTEPS,
        choices=list(TIMESTEP_PRESETS),
        help="Total environment interaction steps.",
    )
    parser.add_argument(
        "--eval-episodes",
        type=int,
        default=20,
        dest="eval_episodes",
        help="Number of evaluation episodes after training.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=100,
        dest="max_steps",
        help="Maximum steps per episode.",
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=3e-4,
        dest="learning_rate",
        help="PPO Adam learning rate.",
    )
    parser.add_argument(
        "--n-steps",
        type=int,
        default=2048,
        dest="n_steps",
        help="PPO rollout buffer size.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        dest="batch_size",
        help="PPO mini-batch size.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        dest="log_level",
        help="Logging verbosity.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()

    # Configure log level from CLI
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    result = main(
        total_timesteps=args.timesteps,
        n_eval_episodes=args.eval_episodes,
        max_steps_per_episode=args.max_steps,
        agent_kwargs={
            "learning_rate": args.learning_rate,
            "n_steps":       args.n_steps,
            "batch_size":    args.batch_size,
            "seed":          args.seed,
        },
    )

    print("\nPipeline result keys:", list(result.keys()))
    print("Saved artefacts:")
    for name, path in result["saved_artefacts"].items():
        print(f"  {name:<35} {path}")
