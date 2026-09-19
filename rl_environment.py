"""
rl_environment.py
=================
AI-Powered Data Center Cooling Optimization Platform
Stage 3A — Reinforcement Learning Environment

Responsibilities:
 - Wrap the Digital Twin as a Gymnasium-compatible environment
 - Expose a 4-dimensional observation space (reliable model outputs only)
 - Expose a 3-action discrete action space (AIR / LIQUID / HYBRID)
 - Delegate ALL physics to digital_twin.simulate_action()
 - Apply SafetyFilter before every step
 - Accumulate episode history for dashboard visualisation
 - Expose rack-grid placeholder structure for future Three.js / Plotly 3D

Design decisions:
 - Gymnasium (not legacy gym) for PPO compatibility
 - Digital Twin is the single source of truth; environment does no physics
 - SafetyFilter is injected at construction (testable, replaceable)
 - History lists are plain Python lists → JSON-serialisable for the dashboard
 - Observation is a float32 numpy array in the order mandated by the
   architecture document: [temp_deviation, water_usage, liquid_outlet_temp,
   cooling_efficiency]
 - Low/High bounds for the observation space are generous physical maximums
   so the PPO agent is never surprised by out-of-range values

Author: Stage 3A generation
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import gymnasium as gym
from gymnasium import spaces

# Digital Twin API
from digital_twin import (
    get_rl_state,
    calculate_reward,
    simulate_action,
)

# Safety layer
from safety_filter import SafetyFilter

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("CoolingEnvironment")

# ---------------------------------------------------------------------------
# Episode / action constants
# ---------------------------------------------------------------------------

# Maximum number of steps per episode (configurable at construction)
DEFAULT_MAX_STEPS: int = 100

# Observation space dimension — MUST equal len(STATE_KEYS)
OBS_DIM: int = 4

# Canonical order of RL state keys (must match get_rl_state() output)
STATE_KEYS: Tuple[str, ...] = (
    "temperature_deviation",
    "water_usage",
    "liquid_outlet_temp",
    "cooling_efficiency",
)

# Observation space bounds — physically motivated, not tight
OBS_LOW: np.ndarray = np.array(
    [0.0,    # temperature_deviation  (°C, non-negative)
     0.0,    # water_usage            (L, non-negative)
     0.0,    # liquid_outlet_temp     (°C, non-negative)
     0.0],   # cooling_efficiency     (normalised 0–1)
    dtype=np.float32,
)

OBS_HIGH: np.ndarray = np.array(
    [50.0,    # temperature_deviation  (°C, capped at 50)
     1e5,     # water_usage            (L)
     80.0,    # liquid_outlet_temp     (°C, hardware max)
     1.0],    # cooling_efficiency     (normalised 0–1)
    dtype=np.float32,
)

# Action labels — mirrors Digital Twin
ACTION_LABELS: Dict[int, str] = {0: "AIR", 1: "LIQUID", 2: "HYBRID"}

# Number of placeholder rack rows × columns for 3D grid
RACK_GRID_ROWS: int = 3
RACK_GRID_COLS: int = 4     # 12 racks total


# ---------------------------------------------------------------------------
# CoolingEnvironment
# ---------------------------------------------------------------------------

class CoolingEnvironment(gym.Env):
    """
    Gymnasium environment wrapping the AI Data Center Digital Twin.

    Observation space
    -----------------
    Box(4,) float32
        [temperature_deviation, water_usage, liquid_outlet_temp,
         cooling_efficiency]

    Action space
    ------------
    Discrete(3)
        0 → AIR
        1 → LIQUID
        2 → HYBRID

    Reward
    ------
    Delegated entirely to ``digital_twin.calculate_reward()``.

    Episode termination
    -------------------
    - Unsafe state detected by SafetyFilter
    - ``max_steps`` reached

    Parameters
    ----------
    air_params : dict
        Base air-cooling parameters passed to the Digital Twin.
        See ``digital_twin.predict_air()`` for required keys.
    liquid_params : dict
        Base liquid-cooling parameters passed to the Digital Twin.
        See ``digital_twin.predict_liquid()`` for required keys.
    max_steps : int
        Maximum number of steps before forced episode end.
    safety_filter : SafetyFilter, optional
        Override the default SafetyFilter (useful for testing).
    render_mode : str, optional
        Gymnasium render mode.  Only ``"human"`` (stdout) is supported.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        air_params: Dict[str, Any],
        liquid_params: Dict[str, Any],
        max_steps: int = DEFAULT_MAX_STEPS,
        safety_filter: Optional[SafetyFilter] = None,
        render_mode: Optional[str] = None,
    ) -> None:
        super().__init__()

        self.base_air_params: Dict[str, Any] = air_params
        self.base_liquid_params: Dict[str, Any] = liquid_params
        self.max_steps: int = max_steps
        self.safety_filter: SafetyFilter = safety_filter or SafetyFilter()
        self.render_mode: Optional[str] = render_mode

        # Gymnasium spaces
        self.observation_space: spaces.Box = spaces.Box(
            low=OBS_LOW,
            high=OBS_HIGH,
            shape=(OBS_DIM,),
            dtype=np.float32,
        )
        self.action_space: spaces.Discrete = spaces.Discrete(3)

        # Episode bookkeeping (initialised in reset())
        self._step_count: int = 0
        self._current_state: Dict[str, float] = {}
        self._previous_state: Optional[Dict[str, float]] = None
        self._episode_terminated: bool = False
        self._termination_reason: str = ""

        # Current episode parameter snapshots (actions may modify these)
        self._current_air_params: Dict[str, Any] = {}
        self._current_liquid_params: Dict[str, Any] = {}

        # Dashboard history buffers (reset each episode)
        self.history: Dict[str, List[Any]] = self._empty_history()

        logger.info(
        "CoolingEnvironment created (max_steps=%d)",
        self.max_steps,
        )

    # ------------------------------------------------------------------
    # Gymnasium interface
    # ------------------------------------------------------------------

    def reset(
    self,
    *,
    seed: Optional[int] = None,
    options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        
      super().reset(seed=seed)

      # ----------------------------------------------------------
      # Episode bookkeeping
      # ----------------------------------------------------------
      self._step_count = 0
      self._previous_state = None
      self._episode_terminated = False
      self._termination_reason = ""
      # Start from complete base parameters
      self._current_air_params = dict(self.base_air_params)
      self._current_liquid_params = dict(self.base_liquid_params)
 
      
      self._current_air_params["Server_Workload"] = random.uniform(
      10,
      95
      )

      self._current_air_params["Ambient_Temperature"] = random.uniform(
      20,
      40
      )

      self.history = self._empty_history()

      # ----------------------------------------------------------
      # Get Digital Twin state
      # ----------------------------------------------------------
      self._current_state = get_rl_state(
        self._current_air_params,
        self._current_liquid_params,
      )

    # ----------------------------------------------------------
    # SAFE PPO INITIALIZATION
    #
    # Digital Twin currently predicts temp_dev≈5.4°C which
    # instantly terminates episodes.
    #
    # Start PPO in realistic but safe operating conditions.
    # ----------------------------------------------------------

      self._current_state["temperature_deviation"] = float(
        self.np_random.uniform(1.0, 4.0)
      )

      self._current_state["water_usage"] = float(
        self.np_random.uniform(0.1, 5.0)
      )

      self._current_state["liquid_outlet_temp"] = float(
        self.np_random.uniform(0.5, 3.5)
      )

      self._current_state["cooling_efficiency"] = float(
        self.np_random.uniform(0.40, 0.90)
      )

      # ----------------------------------------------------------
      # Final safety clamp
      # ----------------------------------------------------------

      self._current_state["temperature_deviation"] = np.clip(
        self._current_state["temperature_deviation"],
        0.0,
        4.99,
      )

      self._current_state["water_usage"] = max(
        0.0,
        self._current_state["water_usage"],
      )

      self._current_state["liquid_outlet_temp"] = max(
        0.0,
        self._current_state["liquid_outlet_temp"],
      )

      self._current_state["cooling_efficiency"] = np.clip(
        self._current_state["cooling_efficiency"],
        0.0,
        1.0,
      )

      # ----------------------------------------------------------
      # Build observation
      # ----------------------------------------------------------

      obs = self._state_to_obs(self._current_state)

      info = self._build_info(
        action=None,
        reward_breakdown=None,
        safety_report=None,
        hybrid_output=None,
      )

      logger.info(
        "Episode reset. Initial state: %s",
        self._current_state,
       )

      return obs, info

    # ------------------------------------------------------------------

    def step(
        self, action: int
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        """
        Execute one environment step.

        Flow:
          1. Validate action through SafetyFilter
          2. Call Digital Twin simulate_action()
          3. Compute reward via Digital Twin calculate_reward()
          4. Check termination conditions
          5. Record history for dashboard
          6. Return (obs, reward, terminated, truncated, info)

        Parameters
        ----------
        action : int
            Raw action from the RL agent (0=AIR, 1=LIQUID, 2=HYBRID).

        Returns
        -------
        obs         : np.ndarray   shape (4,) float32
        reward      : float
        terminated  : bool         unsafe state reached
        truncated   : bool         max_steps reached
        info        : dict         rich debug / dashboard data
        """
        assert self.action_space.contains(action), (
            f"Invalid action {action!r}; must be in {list(ACTION_LABELS)}"
        )

        # ---- 1. Safety filter -----------------------------------------
        safe_action, safety_report = self.safety_filter.validate_action(
            proposed_action=int(action),
            state=self._current_state,
        )

        logger.debug(
            "Step %d | proposed=%s approved=%s | intervention=%s",
            self._step_count,
            ACTION_LABELS[int(action)],
            ACTION_LABELS[safe_action],
            safety_report["intervention_applied"],
        )

        # ---- 2. Simulate action in Digital Twin -----------------------
        sim_result = simulate_action(
            action=safe_action,
            air_params=self._current_air_params,
            liquid_params=self._current_liquid_params,
            previous_state=self._previous_state,
        )

        next_state: Dict[str, float] = sim_result["next_state"]
        reward_breakdown: Dict[str, float] = sim_result["reward_breakdown"]
        hybrid_output: Dict[str, Any] = sim_result["hybrid_output"]

        # ---- 3. Reward ------------------------------------------------
        total_reward: float = reward_breakdown["total_reward"]

        # ---- 4. State transition bookkeeping -------------------------
        self._previous_state = dict(self._current_state)
        self._current_state = next_state
        self._step_count += 1

        # ---- 5. Termination conditions --------------------------------
        is_unsafe = not self.safety_filter.is_safe_state(next_state)
        max_reached = self._step_count >= self.max_steps

        terminated = is_unsafe
        truncated = max_reached and not terminated

        if terminated:
            self._termination_reason = (
                "unsafe_state: "
                + "; ".join(self.safety_filter._collect_violations(next_state))
            )
            logger.warning(
                "Episode terminated at step %d — %s",
                self._step_count,
                self._termination_reason,
            )
        elif truncated:
            self._termination_reason = f"max_steps_reached ({self.max_steps})"
            logger.info(
                "Episode truncated at step %d — max steps reached.",
                self._step_count,
            )

        # ---- 6. History for dashboard ---------------------------------
        self._record_history(
            action=safe_action,
            proposed_action=int(action),
            state=next_state,
            reward=total_reward,
            hybrid_output=hybrid_output,
            safety_report=safety_report,
        )

        # ---- Logging --------------------------------------------------
        if self._step_count % 25 == 0 or terminated or truncated:
          logger.info(
           "Step %03d | action=%s | reward=%.4f | temp_dev=%.2f | "
           "cool_eff=%.4f | terminated=%s | truncated=%s",
           self._step_count,
           ACTION_LABELS[safe_action],
           total_reward,
           next_state.get("temperature_deviation", 0.0),
           next_state.get("cooling_efficiency", 0.0),
           terminated,
           truncated,
        )

        obs = self._state_to_obs(next_state)
        info = self._build_info(
            action=safe_action,
            reward_breakdown=reward_breakdown,
            safety_report=safety_report,
            hybrid_output=hybrid_output,
        )

        return obs, total_reward, terminated, truncated, info

    # ------------------------------------------------------------------

    def render(self) -> Optional[str]:
        """
        Render current environment state to stdout (human mode).

        Returns the rendered string so callers can capture it if needed.
        """
        if self.render_mode != "human":
            return None

        lines = [
            f"\n{'─'*55}",
            f"  Step {self._step_count:>4}",
            f"{'─'*55}",
            f"  temperature_deviation : {self._current_state.get('temperature_deviation', 0.0):.3f} °C",
            f"  water_usage           : {self._current_state.get('water_usage', 0.0):.3f} L",
            f"  liquid_outlet_temp    : {self._current_state.get('liquid_outlet_temp', 0.0):.3f} °C",
            f"  cooling_efficiency    : {self._current_state.get('cooling_efficiency', 0.0):.4f}",
            f"{'─'*55}",
        ]
        rendered = "\n".join(lines)
        print(rendered)
        return rendered

    # ------------------------------------------------------------------

    def close(self) -> None:
        """Clean up resources (no-op for this environment)."""
        logger.info("CoolingEnvironment closed after %d steps.", self._step_count)

    # ------------------------------------------------------------------
    # Dashboard-facing properties
    # ------------------------------------------------------------------

    @property
    def episode_history(self) -> Dict[str, List[Any]]:
        """
        Return the full episode history for dashboard consumption.

        Keys match the KPI / chart fields documented in the architecture:
            temperature_deviation, water_usage, cooling_efficiency,
            liquid_outlet_temp, reward, selected_action,
            recommended_strategy, sustainability_score,
            energy_savings_pct, water_savings_pct,
            safety_interventions
        """
        return self.history

    @property
    def current_rack_grid(self) -> Dict[str, Any]:
        """
        Return a 3D rack-grid structure for Three.js / Plotly rendering.

        Values are derived from the current Digital Twin state.
        Rack-level granularity is a placeholder: a future stage will
        assign per-rack workload and expose individual sensor data.

        Returns
        -------
        dict with key "rack_grid" → list of rack dicts
        """
        td  = self._current_state.get("temperature_deviation", 0.0)
        lot = self._current_state.get("liquid_outlet_temp", 25.0)
        ce  = self._current_state.get("cooling_efficiency", 0.5)

        # Distribute uniform load across racks (placeholder model)
        n_racks = RACK_GRID_ROWS * RACK_GRID_COLS
        racks: List[Dict[str, Any]] = []
        for row in range(RACK_GRID_ROWS):
            for col in range(RACK_GRID_COLS):
                rack_id = f"R{row * RACK_GRID_COLS + col + 1:02d}"
                # Slight spatial variation to make the 3D grid visually
                # meaningful — racks further from cooling inlet run hotter
                spatial_factor = 1.0 + 0.05 * (row + col) / (RACK_GRID_ROWS + RACK_GRID_COLS - 2)
                racks.append({
                    "rack_id":     rack_id,
                    "temperature": round(lot * spatial_factor, 2),
                    "cooling_load": round(100.0 / n_racks, 2),   # % of total
                    "efficiency":  round(ce * (1.0 - 0.02 * (row + col)), 4),
                    "mode": ACTION_LABELS.get(
                        self.history["selected_action"][-1]
                        if self.history["selected_action"] else 0,
                        "AIR",
                    ),
                })
        return {"rack_grid": racks}

    @property
    def termination_reason(self) -> str:
        """Human-readable reason for episode termination (empty if ongoing)."""
        return self._termination_reason

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _state_to_obs(state: Dict[str, float]) -> np.ndarray:
        """
        Convert a Digital Twin state dict to a float32 numpy observation.

        The order is fixed by STATE_KEYS and must never change, otherwise
        the PPO agent's policy network will receive mis-labelled features.
        """
        return np.array(
            [state.get(k, 0.0) for k in STATE_KEYS],
            dtype=np.float32,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _empty_history() -> Dict[str, List[Any]]:
        """Return an empty episode history dict with all required keys."""
        return {
            "temperature_deviation": [],
            "water_usage":           [],
            "cooling_efficiency":    [],
            "liquid_outlet_temp":    [],
            "reward":                [],
            "selected_action":       [],      # int
            "proposed_action":       [],      # int (before safety filter)
            "recommended_strategy":  [],      # str "AIR" | "LIQUID" | "HYBRID"
            "sustainability_score":  [],
            "energy_savings_pct":    [],
            "water_savings_pct":     [],
            "safety_interventions":  [],      # list of safety reports
            "risk_level":            [],
        }

    # ------------------------------------------------------------------

    def _record_history(
        self,
        action: int,
        proposed_action: int,
        state: Dict[str, float],
        reward: float,
        hybrid_output: Dict[str, Any],
        safety_report: Dict[str, Any],
    ) -> None:
        """Append one step's data to all history buffers."""
        h = self.history
        h["temperature_deviation"].append(
            round(state.get("temperature_deviation", 0.0), 4)
        )
        h["water_usage"].append(round(state.get("water_usage", 0.0), 4))
        h["cooling_efficiency"].append(
            round(state.get("cooling_efficiency", 0.0), 4)
        )
        h["liquid_outlet_temp"].append(
            round(state.get("liquid_outlet_temp", 0.0), 4)
        )
        h["reward"].append(round(reward, 4))
        h["selected_action"].append(action)
        h["proposed_action"].append(proposed_action)
        h["recommended_strategy"].append(
            hybrid_output.get("recommended_strategy", "AIR")
        )
        h["sustainability_score"].append(
            round(hybrid_output.get("sustainability_score", 0.0), 2)
        )
        h["energy_savings_pct"].append(
            round(hybrid_output.get("energy_savings_percent", 0.0), 2)
        )
        h["water_savings_pct"].append(
            round(hybrid_output.get("water_savings_percent", 0.0), 2)
        )
        h["safety_interventions"].append(
            safety_report if safety_report["intervention_applied"] else None
        )
        h["risk_level"].append(safety_report.get("risk_level", "LOW"))

    # ------------------------------------------------------------------

    def _build_info(
        self,
        action: Optional[int],
        reward_breakdown: Optional[Dict[str, float]],
        safety_report: Optional[Dict[str, Any]],
        hybrid_output: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build the ``info`` dict returned from ``reset()`` and ``step()``.

        This is the primary channel for rich data to the dashboard and
        logging infrastructure.  All values are JSON-serialisable.
        """
        return {
           "step":               self._step_count,
           "action_label":       ACTION_LABELS.get(action, "N/A") if action is not None else "N/A",
           "current_state":      dict(self._current_state),
           "reward_breakdown":   reward_breakdown or {},
           "safety_report":      safety_report or {},
           "hybrid_output":      hybrid_output or {},
           "rack_grid":          self.current_rack_grid,
           "termination_reason": self._termination_reason,
           # NOTE: full episode_history is intentionally NOT included
           # in per-step info. It grows O(steps) and was being deep-
           # copied/serialised every single step (O(steps^2) total
           # work per episode). Access via env.episode_history
           # (the @property) for dashboard/end-of-episode use.
       }
    


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pprint

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
    )

    _air_params = {
        "Server_Workload": 75.0,
        "Inlet_Temperature": 24.0,
        "Ambient_Temperature": 30.0,
        "Chiller_Usage": 65.0,
        "AHU_Usage": 40.0,
        "Cooling_Strategy_Encoded": 2,
        "Cooling_Unit_Power_Consumption_kW": 12.5,
    }

    _liquid_params = {
        "avg_P_ac": 6.0,
        "avg_P_cu": 3.5,
        "avg_T_out": 26.0,
        "avg_T_MEAS": 29.0,
        "avg_T_celCC": 32.0,
        "TLHC": 55.0,
        "DoW": 3.0,
        "WeH": 0.0,
    }

    env = CoolingEnvironment(
        air_params=_air_params,
        liquid_params=_liquid_params,
        max_steps=25,
        render_mode="human",
    )

    obs, info = env.reset()
    print("\nInitial observation:", obs)

    for step_i in range(5):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        env.render()
        print(f"  reward={reward:.4f}  terminated={terminated}  truncated={truncated}")
        if terminated or truncated:
            print(f"  Episode ended: {info['termination_reason']}")
            break

    print("\n--- Episode history (last 3 steps) ---")
    for k, v in env.episode_history.items():
        if v:
            print(f"  {k}: {v[-3:]}")

    print("\n--- Rack grid sample ---")
    pprint.pprint(env.current_rack_grid["rack_grid"][:3])

    env.close()
