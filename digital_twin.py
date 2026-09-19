"""
digital_twin.py
===============
AI-Powered Data Center Cooling Optimization Platform
Stage 3 — Digital Twin Inference Engine

Responsibilities:
  - Load all trained XGBoost models from models/
  - Load model_metadata.json for confidence scoring
  - Expose predict_air(), predict_liquid(), predict_hybrid()
  - Expose RL hooks: get_rl_state(), calculate_reward(), simulate_action()
  - Return dashboard-ready, JSON-serializable dicts
  - Never crash on missing optional inputs

Author: Stage 3 generation
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd

import numpy as np
import pickle

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger("DigitalTwin")


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
METADATA_PATH = BASE_DIR / "models" / "model_metadata.json"


# ---------------------------------------------------------------------------
# R² reference — used as fallback if metadata file is absent
# ---------------------------------------------------------------------------
_R2_REFERENCE: Dict[str, float] = {
    "air_outlet_temperature": 0.5357,   # FAILED
    "air_energy_cost":        0.4230,   # FAILED
    "air_temp_deviation":     0.9975,   # PASSED
    "air_water_usage":        0.9517,   # PASSED
    "liquid_avg_t_out":       0.7957,   # PASSED
    "liquid_stability":       0.2983,   # FAILED
    "liquid_efficiency":      0.9691,   # PASSED
}

# R² → confidence tier
def _r2_to_confidence(r2: float) -> str:
    if r2 >= 0.75:
        return "HIGH"
    if r2 >= 0.60:
        return "MEDIUM"
    return "LOW"

# Models that are safe for RL (R² >= 0.75)
RL_RELIABLE_MODELS = {k for k, v in _R2_REFERENCE.items() if v >= 0.75}


# ---------------------------------------------------------------------------
# Physical bounds — clamp predictions to physically plausible ranges
# ---------------------------------------------------------------------------
_BOUNDS: Dict[str, tuple[float, float]] = {
    "outlet_temperature":  (10.0,  90.0),   # °C
    "energy_cost":         (0.0,   1e6),    # $
    "temperature_deviation":(0.0,  50.0),   # °C
    "water_usage":         (0.0,   1e5),    # L
    "avg_outlet_temp":     (5.0,   80.0),   # °C
    "thermal_stability":   (0.0,   1.0),    # score 0–1
    "cooling_efficiency":  (0.0,   1.0),    # score 0–1
    "water_savings_percent":(0.0,  100.0),
    "energy_savings_percent":(0.0, 100.0),
    "sustainability_score": (0.0,  100.0),
}

def _clamp(value: float, key: str) -> float:
    lo, hi = _BOUNDS.get(key, (-1e12, 1e12))
    return float(np.clip(value, lo, hi))


# ---------------------------------------------------------------------------
# Model loader
# ---------------------------------------------------------------------------
class _ModelRegistry:
    """Loads and caches all XGBoost pkl models + metadata once."""

    def __init__(self) -> None:
        self._models: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._confidence: Dict[str, str] = {}
        self._loaded = False

    # ------------------------------------------------------------------
    def _load_metadata(self) -> None:
        if METADATA_PATH.exists():
            with open(METADATA_PATH, "r") as f:
                self._metadata = json.load(f)
            logger.info("Loaded model_metadata.json")
        else:
            logger.warning(
                "model_metadata.json not found — using built-in R² reference."
            )
            self._metadata = {}

        # Build confidence map — prefer metadata values, fall back to reference
        for model_key, r2_default in _R2_REFERENCE.items():
            r2 = (
                self._metadata.get(model_key, {}).get("r2", r2_default)
                if self._metadata
                else r2_default
            )
            self._confidence[model_key] = _r2_to_confidence(r2)

    # ------------------------------------------------------------------
    def _load_model(self, filename: str, model_key: str) -> None:
        path = MODELS_DIR / filename
        if path.exists():
            with open(path, "rb") as f:
                self._models[model_key] = pickle.load(f)
            logger.info("Loaded model: %s (confidence=%s)", filename, self._confidence.get(model_key, "?"))
        else:
            logger.error("Model file NOT FOUND: %s", path)
            self._models[model_key] = None

    # ------------------------------------------------------------------
    def load_all(self) -> None:
        if self._loaded:
            return
        self._load_metadata()
        self._load_model("xgb_air_outlet_temperature.pkl", "air_outlet_temperature")
        self._load_model("xgb_air_energy_cost.pkl",        "air_energy_cost")
        self._load_model("xgb_air_temp_deviation.pkl",     "air_temp_deviation")
        self._load_model("xgb_air_water_usage.pkl",        "air_water_usage")
        self._load_model("xgb_liquid_avg_t_out.pkl",       "liquid_avg_t_out")
        self._load_model("xgb_liquid_stability.pkl",       "liquid_stability")
        self._load_model("xgb_liquid_efficiency.pkl",      "liquid_efficiency")
        self._loaded = True
        logger.info("All models loaded. RL-reliable: %s", sorted(RL_RELIABLE_MODELS))

    # ------------------------------------------------------------------
    def predict(self, model_key: str, features: Dict[str, float]) -> Optional[float]:

        model = self._models.get(model_key)

        if model is None:
            logger.warning("Model '%s' is not loaded — returning None.", model_key)
            return None
        
        try:
            expected_features = list(model.feature_names_in_)
            X = pd.DataFrame([features])
            X = X.reindex(columns=expected_features)
            result = model.predict(X)
            return float(result[0])
            
        except Exception as exc:
            print("\n" + "=" * 80)
            print("PREDICTION ERROR")
            print("MODEL :", model_key)
            print("ERROR :", exc)
            print("=" * 80 + "\n")

            raise
        

    # ------------------------------------------------------------------
    def confidence(self, model_key: str) -> str:
        return self._confidence.get(model_key, "UNKNOWN")


# Singleton registry
_registry = _ModelRegistry()


def _ensure_loaded() -> None:
    _registry.load_all()


# ---------------------------------------------------------------------------
# Feature engineering helpers (replicate Stage 1 logic for inference)
# ---------------------------------------------------------------------------

def _compute_air_derived_features(params: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute engineered air features from raw inputs.
    Uses defaults of 0 for any optional field not provided.
    """
    workload    = float(params.get("Server_Workload", 50.0))
    inlet_temp  = float(params.get("Inlet_Temperature", 22.0))
    ambient     = float(params.get("Ambient_Temperature", 25.0))
    chiller     = float(params.get("Chiller_Usage", 50.0))
    ahu         = float(params.get("AHU_Usage", 50.0))
    cooling_enc = float(params.get("Cooling_Strategy_Encoded", 0.0))
    cup_kw      = float(params.get("Cooling_Unit_Power_Consumption_kW", 10.0))
    hour = float(params.get("Hour", 12))
    day_of_week = float(params.get("DayOfWeek", 3))
    month = float(params.get("Month", 6))

    total_cooling   = chiller + ahu + 1e-9
    cooling_eff     = params.get("Cooling_Efficiency",
                                  workload / total_cooling if total_cooling else 0.0)
    cooling_ratio   = params.get("Cooling_Ratio",
                                  chiller / (ahu + 1e-9))
    amb_inlet_delta = params.get("Ambient_Inlet_Delta",
                                  inlet_temp - ambient )
    energy_per_wl   = params.get("Energy_per_Workload",
                                  cup_kw / (workload + 1e-9))
    water_est       = params.get("Water_Usage_Estimate",
                                  chiller * 0.5)
    heat_load_idx   = params.get("Heat_Load_Index",
                                  workload * (ambient - 18.0))

    return {
        "Server_Workload":                  workload,
        "Inlet_Temperature":                inlet_temp,
        "Ambient_Temperature":              ambient,
        "Chiller_Usage":                    chiller,
        "AHU_Usage":                        ahu,
        "Cooling_Strategy_Encoded":         cooling_enc,
        "Cooling_Efficiency":               float(cooling_eff),
        "Cooling_Ratio":                    float(cooling_ratio),
        "Ambient_Inlet_Delta":              float(amb_inlet_delta),
        "Energy_per_Workload":              float(energy_per_wl),
        "Water_Usage_Estimate":             float(water_est),
        "Heat_Load_Index":                  float(heat_load_idx),
        "Cooling_Unit_Power_Consumption_kW": cup_kw,
    }


# Stage 1 air feature order — MUST match training column order
_AIR_FEATURE_ORDER = [
    "Server_Workload",
    "Inlet_Temperature",
    "Ambient_Temperature",
    "Chiller_Usage",
    "AHU_Usage",
    "Cooling_Strategy_Encoded",
    "Cooling_Efficiency",
    "Cooling_Ratio",
    "Ambient_Inlet_Delta",
    "Energy_per_Workload",
    "Water_Usage_Estimate",
    "Heat_Load_Index",
    "Cooling_Unit_Power_Consumption_kW",
]

# Stage 1 liquid feature order — MUST match training column order
_LIQUID_FEATURE_ORDER = [
    "avg_P_ac",
    "avg_P_cu",
    "avg_T_out",
    "avg_T_MEAS",
    "avg_T_celCC",
    "delta_T_out_meas",
    "delta_T_meas_cell",
    "thermal_stability_score",
    "cooling_efficiency_score",
    "TLHC",
    "DoW",
    "WeH",
]


def _compute_liquid_derived_features(params: Dict[str, Any]) -> Dict[str, float]:
    """
    Compute engineered liquid features from raw inputs.
    delta_T and scores are derived if not supplied.
    """
    p_ac      = float(params.get("avg_P_ac", 5.0))
    p_cu      = float(params.get("avg_P_cu", 3.0))
    t_out     = float(params.get("avg_T_out", 25.0))
    t_meas    = float(params.get("avg_T_MEAS", 28.0))
    t_celCC   = float(params.get("avg_T_celCC", 30.0))
    tlhc      = float(params.get("TLHC", 50.0))
    dow       = float(params.get("DoW", 1.0))
    weh       = float(params.get("WeH", 0.0))

    delta_t_out_meas   = params.get("delta_T_out_meas",   t_meas  - t_out)
    delta_t_meas_cell  = params.get("delta_T_meas_cell",  t_celCC - t_meas)
    thermal_stability  = params.get("thermal_stability_score",
                                    1.0 / (1.0 + abs(float(delta_t_meas_cell))))
    cooling_eff_score  = params.get("cooling_efficiency_score",
                                    p_cu / (p_ac + 1e-9))

    return {
        "avg_P_ac":               p_ac,
        "avg_P_cu":               p_cu,
        "avg_T_out":              t_out,
        "avg_T_MEAS":             t_meas,
        "avg_T_celCC":            t_celCC,
        "delta_T_out_meas":       float(delta_t_out_meas),
        "delta_T_meas_cell":      float(delta_t_meas_cell),
        "thermal_stability_score":float(thermal_stability),
        "cooling_efficiency_score":float(cooling_eff_score),
        "TLHC":                   tlhc,
        "DoW":                    dow,
        "WeH":                    weh,
    }


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def _validate_air_input(params: Dict[str, Any]) -> None:
    required = {"Server_Workload", "Inlet_Temperature", "Ambient_Temperature"}
    missing = required - params.keys()
    if missing:
        raise ValueError(f"predict_air() missing required fields: {missing}")
    if not (0 <= params["Server_Workload"] <= 100):
        raise ValueError("Server_Workload must be in [0, 100]")
    if not (-10 <= params["Inlet_Temperature"] <= 50):
        raise ValueError("Inlet_Temperature must be in [-10, 50]°C")


def _validate_liquid_input(params: Dict[str, Any]) -> None:
    required = {"avg_P_ac", "avg_P_cu", "avg_T_MEAS", "avg_T_celCC"}
    missing = required - params.keys()
    if missing:
        raise ValueError(f"predict_liquid() missing required fields: {missing}")


# ---------------------------------------------------------------------------
# PUBLIC PREDICTION FUNCTIONS
# ---------------------------------------------------------------------------

def predict_air(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict air-cooling outcomes from sensor/workload inputs.
    """
    _ensure_loaded()
    _validate_air_input(params)

    # Compute Stage-1 engineered features
    feats = _compute_air_derived_features(params)

    # Model predictions
    outlet_temp = _registry.predict(
        "air_outlet_temperature",
        feats
    )

    energy_cost = _registry.predict(
        "air_energy_cost",
        feats
    )

    temp_dev = _registry.predict(
        "air_temp_deviation",
        feats
    )

    water_usage = _registry.predict(
        "air_water_usage",
        feats
    )

    # Apply physical bounds
    outlet_temp = (
        _clamp(outlet_temp, "outlet_temperature")
        if outlet_temp is not None else None
    )

    energy_cost = (
        _clamp(energy_cost, "energy_cost")
        if energy_cost is not None else None
    )

    temp_dev = (
        _clamp(temp_dev, "temperature_deviation")
        if temp_dev is not None else None
    )

    water_usage = (
        _clamp(water_usage, "water_usage")
        if water_usage is not None else None
    )

    return {
        "outlet_temperature": outlet_temp,
        "energy_cost": energy_cost,
        "temperature_deviation": temp_dev,
        "water_usage": water_usage,
        "confidence": {
            "outlet_temperature":
                _registry.confidence("air_outlet_temperature"),

            "energy_cost":
                _registry.confidence("air_energy_cost"),

            "temperature_deviation":
                _registry.confidence("air_temp_deviation"),

            "water_usage":
                _registry.confidence("air_water_usage"),
        },
    }


def predict_liquid(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict liquid-cooling outcomes.

    Parameters
    ----------
    params : dict
        Must contain: avg_P_ac, avg_P_cu, avg_T_MEAS, avg_T_celCC
        Optional: avg_T_out, TLHC, DoW, WeH, delta_* fields, score fields.

    Returns
    -------
    dict  (dashboard-ready, JSON-serializable)
    """
    _ensure_loaded()
    _validate_liquid_input(params)

    feats = _compute_liquid_derived_features(params)

    avg_t_out = _registry.predict(
    "liquid_avg_t_out",
    feats
    )

    stability = _registry.predict(
    "liquid_stability",
    feats
    )

    efficiency = _registry.predict(
    "liquid_efficiency",
    feats
    )

    avg_t_out = (
    float(avg_t_out)
    if avg_t_out is not None else None
  )


    stability = (
    float(stability)
    if stability is not None else None
    )

    if efficiency is not None:
     efficiency = _clamp(
        float(efficiency) / 10.0,
        "cooling_efficiency",
     )

    return {
        "avg_outlet_temp":   avg_t_out,
        "thermal_stability": stability,
        "cooling_efficiency":efficiency,
        "confidence": {
            "avg_outlet_temp":   _registry.confidence("liquid_avg_t_out"),
            "thermal_stability": _registry.confidence("liquid_stability"),
            "cooling_efficiency":_registry.confidence("liquid_efficiency"),
        },
    }


def predict_hybrid(
    air_params: Dict[str, Any],
    liquid_params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Hybrid prediction layer — combines air + liquid model outputs.

    Computes:
      - water_savings_percent
      - energy_savings_percent
      - sustainability_score   (0–100, ready for gauge widget)
      - recommended_strategy   ("AIR" | "LIQUID" | "HYBRID")

    Parameters
    ----------
    air_params    : dict   Same input schema as predict_air()
    liquid_params : dict   Same input schema as predict_liquid()

    Returns
    -------
    dict  (dashboard-ready, JSON-serializable)
    """
    _ensure_loaded()

    air_out    = predict_air(air_params)
    liquid_out = predict_liquid(liquid_params)

    water_usage    = air_out.get("water_usage")    or 0.0
    temp_deviation = air_out.get("temperature_deviation") or 0.0
    energy_cost    = air_out.get("energy_cost")    or 0.0

    cooling_eff = liquid_out.get("cooling_efficiency") or 0.0

    # ---- Water savings -------------------------------------------------
    # Baseline: air-only water_usage; hybrid achieves liquid_efficiency gain
    # water_savings = (1 - (1 - cooling_eff)) * 100 normalised to dataset max
    baseline_water = max(water_usage, 1.0)
    hybrid_water   = baseline_water * (1.0 - min(cooling_eff, 0.99))
    water_savings_pct = _clamp(
        ((baseline_water - hybrid_water) / baseline_water) * 100.0,
        "water_savings_percent",
    )

    # ---- Energy savings ------------------------------------------------
    # Better cooling efficiency → less energy waste
    # Rough model: 1% cooling_eff improvement ≈ 0.5% energy saving
    energy_savings_pct = _clamp(
        cooling_eff * 50.0,    # max ~50% saving at eff=1.0
        "energy_savings_percent",
    )

    # ---- Temperature penalty -------------------------------------------
    temp_penalty = min(temp_deviation / 10.0, 1.0)   # normalise; cap at 1

    # ---- Sustainability score ------------------------------------------
    # Weighted composite (0–100)
    raw_score = (
        0.40 * water_savings_pct           # water conservation weight
        + 0.30 * energy_savings_pct        # energy efficiency weight
        + 0.30 * (cooling_eff * 100.0)     # cooling quality weight
        - 20.0 * temp_penalty              # temperature deviation penalty
    )
    sustainability_score = _clamp(raw_score, "sustainability_score")

    # ---- Strategy recommendation --------------------------------------
    if water_savings_pct >= 40 and energy_savings_pct >= 30:
        recommended_strategy = "HYBRID"
    elif cooling_eff >= 0.80 and temp_deviation <= 3.0:
        recommended_strategy = "LIQUID"
    else:
        recommended_strategy = "AIR"

    # ---- Merged confidence --------------------------------------------
    confidence = {
        **air_out["confidence"],
        **liquid_out["confidence"],
    }

    return {
        # ---- Air metrics (pass-through for dashboard cards) ----
        "water_usage":           water_usage,
        "energy_cost":           energy_cost,
        "temperature_deviation": temp_deviation,
        "outlet_temperature":    air_out.get("outlet_temperature"),
        # ---- Liquid metrics ----------------------------------------
        "cooling_efficiency":    cooling_eff,
        "avg_outlet_temp":       liquid_out.get("avg_outlet_temp"),
        "thermal_stability":     liquid_out.get("thermal_stability"),
        # ---- Hybrid-specific computed values ----------------------
        "water_savings_percent": round(water_savings_pct, 2),
        "energy_savings_percent":round(energy_savings_pct, 2),
        "sustainability_score":  round(sustainability_score, 2),
        "recommended_strategy":  recommended_strategy,
        # ---- Confidence map ----------------------------------------
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# RL INTEGRATION HOOKS
# ---------------------------------------------------------------------------

def get_rl_state(
    air_params: Dict[str, Any],
    liquid_params: Dict[str, Any],
) -> Dict[str, float]:
    """
    Returns ONLY reliable model outputs for RL agent consumption.

    Reliable models (R² >= 0.75):
        air_temp_deviation  R²=0.9975
        air_water_usage     R²=0.9517
        liquid_avg_t_out    R²=0.7957
        liquid_efficiency   R²=0.9691

    The RL agent MUST use this function — never raw datasets.
    """
    _ensure_loaded()

    air_out    = predict_air(air_params)
    liquid_out = predict_liquid(liquid_params)

    temp_dev   = air_out.get("temperature_deviation") or 0.0
    water_use  = air_out.get("water_usage")           or 0.0
    liq_t_out  = liquid_out.get("avg_outlet_temp")    or 0.0
    # Raw efficiency model output is not normalized.
    # Convert to RL-friendly [0,1] scale before exposing state.
    cool_eff = liquid_out.get(
    "cooling_efficiency",
    0.0,
   )

    return {
    "temperature_deviation": float(temp_dev),
    "water_usage": float(water_use),
    "liquid_outlet_temp": float(liq_t_out),
    "cooling_efficiency": float(cool_eff),
   }



def calculate_reward(
    state: Dict[str, float],
    previous_state: Optional[Dict[str, float]] = None,
    overheating_threshold: float = 5.0,
) -> Dict[str, float]:
    """
    Computes the RL reward from a Digital Twin state dict.

    Reward structure:
        +5  × water_savings          (primary KPI)
        +3  × energy_savings
        +2  × cooling_efficiency
        -10 × temperature_deviation
        -20 × overheating_penalty    (if temp_dev > threshold)

    Parameters
    ----------
    state              : dict   Current RL state (from get_rl_state())
    previous_state     : dict   Previous RL state (optional, for delta rewards)
    overheating_threshold : float   °C deviation above which penalty applies

    Returns
    -------
    dict with 'total_reward' and individual component breakdown
    """
    temp_dev  = state.get("temperature_deviation", 0.0)
    water_use = state.get("water_usage",           0.0)
    cool_eff  = state.get("cooling_efficiency",    0.5)

    # Savings signals — if previous state available, use deltas

    water_savings = 1.0 - min(
    water_use / 0.40,
    1.0,
    )

    energy_savings = cool_eff
    # if previous_state is not None:
    #     prev_water = previous_state.get("water_usage", water_use)
    #     water_savings = max(0.0, (prev_water - water_use) / (prev_water + 1e-9))

    #     prev_eff = previous_state.get("cooling_efficiency", cool_eff)
    #     energy_savings = max(0.0, cool_eff - prev_eff)   # improved efficiency = saved energy
    # else:
    #     # Absolute signal when no prior state

    #     water_savings = 1.0 - min(
    #     water_use / 0.40,
    #     1.0,
    #      )
    #     energy_savings = cool_eff                           # efficiency itself as proxy

    # Overheating penalty
    overheating_penalty = 1.0 if temp_dev > overheating_threshold else 0.0

    # Component rewards
    # -------------------------------------------------
   # REWARD SCALING (v2)
   #
   # Problem: r_temp alone could reach -10/step (at
   # temp_dev == threshold), dwarfing r_water (max +5) and
   # r_efficiency (max +2). Over a 100-step episode this
   # produces large negative returns even for safe operation,
   # and lets the temperature term dominate the gradient.
   #
   # Fix: rescale all components onto a comparable
   # [-2, +2]-ish per-step range BEFORE applying priority
   # weights. Priority order (water > efficiency > energy >
   # temp-as-soft-penalty, with overheating as a sharp but
   # bounded penalty) is preserved via the weight ordering
   # below, but no single component can structurally dominate
   # every episode regardless of behaviour.
   #
   # Priority order requested by spec:
   #   1. Prevent overheating   -> r_overheat (sharp, bounded)
   #   2. Reduce temp deviation -> r_temp (soft, now bounded to [-2,0])
   #   3. Reduce water usage    -> r_water (now the largest positive term)
   #   4. Improve cooling eff   -> r_efficiency
   #   5. Reduce energy         -> r_energy
   # -------------------------------------------------

   # Soft temperature penalty — bounded to [-2, 0] regardless of
   # how large temp_dev/threshold gets (tanh saturates).
   # At temp_dev == threshold: r_temp ≈ -2 * tanh(1) ≈ -1.52
   # At temp_dev == 0:         r_temp = 0
    r_temp = -2.0 * np.tanh(temp_dev / (overheating_threshold + 1e-9))

   # Sharp overheating penalty — kept bounded (was -20, now -5) so
   # one bad step doesn't single-handedly define the episode return,
   # but is still clearly the worst single-step outcome possible.
    r_overheat = -5.0 * overheating_penalty

   # Water savings remains the primary positive KPI (spec priority #3,
   # but now the dominant *positive* signal since temp/overheat are
   # bounded penalties rather than unbounded-feeling negatives).
    r_water = 4.0 * water_savings

   # Cooling efficiency — direct signal, not a delta, so the agent gets
   # consistent feedback on absolute cooling quality every step.
    r_efficiency = 1.5 * cool_eff

   # Energy savings — smallest weight per spec priority #5.
    r_energy = 1.0 * energy_savings

    total_reward = (
       r_overheat + r_temp + r_water + r_efficiency + r_energy
   )

    return {
    "total_reward": float(round(total_reward, 4)),
    "reward_water": float(round(r_water, 4)),
    "reward_energy": float(round(r_energy, 4)),
    "reward_efficiency": float(round(r_efficiency, 4)),
    "reward_temp": float(round(r_temp, 4)),
    "reward_overheat": float(round(r_overheat, 4)),
    "overheating_penalty": bool(overheating_penalty),
   }

def simulate_action(
    action: int,
    air_params: Dict[str, Any],
    liquid_params: Dict[str, Any],
    previous_state: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Simulate an RL action and return next state + reward.

    Action space:
        0 — AIR cooling
        1 — LIQUID cooling
        2 — HYBRID cooling

    The action modifies Cooling_Strategy_Encoded in air_params before
    prediction, so the Digital Twin reflects the chosen mode.

    Returns
    -------
    dict with keys: next_state, reward_breakdown, hybrid_output
    """
    _ensure_loaded()

    if action not in (0, 1, 2):
        raise ValueError(f"Invalid action {action}. Must be 0 (AIR), 1 (LIQUID), or 2 (HYBRID).")

    # Apply action to params
    updated_air = {**air_params, "Cooling_Strategy_Encoded": float(action)}

    # -------------------------------------------------
   # RL ACTION DYNAMICS (v2 — Pareto trade-offs)
   #
   # Design principle: each strategy must be the *best*
   # choice under SOME operating condition, and the *worst*
   # under another. A strategy that dominates on every axis
   # gives PPO no exploration incentive (see Stage 4 review).
   #
   # AIR    — cheapest on water, weakest on temperature control.
   #          Best when ambient is cool / workload is low and
   #          tight temperature control isn't needed.
   # LIQUID — best temperature control and efficiency, but the
   #          most water-intensive. Best under high thermal load
   #          where overheating risk is the dominant concern.
   # HYBRID — balanced; never the best on any single axis but
   #          never the worst either. Best when both water AND
   #          temperature matter roughly equally.
   #
   # Numerically: AIR and LIQUID are now mirror-image trade-offs
   # (AIR favours water at the cost of temp control; LIQUID is the
   # reverse), and HYBRID sits at the midpoint with a small
   # synergy bonus on efficiency to reflect real combined-system
   # behaviour. This creates a genuine 2D Pareto frontier on
   # (temperature_deviation, water_usage), with cooling_efficiency
   # correlated to temperature_deviation control quality.
   # -------------------------------------------------

    hybrid_output = predict_hybrid(updated_air, liquid_params)
    next_state    = get_rl_state(updated_air, liquid_params)

    # -------------------------------------------------
    # OPERATING CONDITIONS
    # -------------------------------------------------

    
    workload = float(
    air_params.get(
        "Server_Workload",
        50.0
     )
    )

    temp_dev = float(
    next_state.get(
        "temperature_deviation",
        0.0
     )
    )

    if action == 0:  # AIR

     # Base behaviour
     next_state["temperature_deviation"] *= 1.08
    #  next_state["water_usage"] *= 0.70
     next_state["water_usage"] *= 0.60
     next_state["cooling_efficiency"] *= 0.92

    # LOW WORKLOAD BONUS
    # if workload < 30:
    #     next_state["cooling_efficiency"] *= 1.05
    #     next_state["temperature_deviation"] *= 0.95
    if workload < 25:
        next_state["cooling_efficiency"] *= 1.04
        next_state["temperature_deviation"] *= 0.97


    elif action == 1:  # LIQUID

     # Base behaviour
     next_state["temperature_deviation"] *= 0.80
     next_state["water_usage"] *= 1.25
     next_state["cooling_efficiency"] *= 1.08

    # HIGH WORKLOAD BONUS
    if workload > 80:
        next_state["cooling_efficiency"] *= 1.10

    # THERMAL EMERGENCY BONUS
    if temp_dev > 5:
        next_state["temperature_deviation"] *= 0.70
        next_state["cooling_efficiency"] *= 1.08


    else:  # HYBRID

     # Balanced operating mode
    #  next_state["temperature_deviation"] *= 0.85
    #  next_state["water_usage"] *= 0.75
    #  next_state["cooling_efficiency"] *= 1.15

     next_state["temperature_deviation"] *= 0.85
     next_state["water_usage"] *= 0.85
     next_state["cooling_efficiency"] *= 1.08

    # HYBRID sweet spot

     # NORMAL OPERATING RANGE BONUS
     # HYBRID should dominate in balanced scenarios
    if 25 <= workload <= 80 and temp_dev <= 5:
       next_state["cooling_efficiency"] *= 1.03

    #  if 40 <= workload <= 70:
    #   next_state["water_usage"] *= 0.90 

    # -------------------------------------------------
    # SAFETY CLAMPS
    # -------------------------------------------------

    next_state["cooling_efficiency"] = min(
        max(next_state["cooling_efficiency"], 0.0),
        1.0,
    )

    next_state["water_usage"] = max(
        next_state["water_usage"],
        0.0,
    )

    reward = calculate_reward(
        next_state,
        previous_state
    )

    return {
        "action":         action,
        "action_label":   ["AIR", "LIQUID", "HYBRID"][action],
        "next_state":     next_state,
        "reward_breakdown": reward,
        "hybrid_output":  hybrid_output,
    }


# ---------------------------------------------------------------------------
# Convenience: load models at import time
# ---------------------------------------------------------------------------
_registry.load_all()


# ---------------------------------------------------------------------------
# Example usage / smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pprint

    print("\n" + "=" * 60)
    print("  Digital Twin — Stage 3 Smoke Test")
    print("=" * 60)

    _air_input = {
        "Server_Workload":      75.0,
        "Inlet_Temperature":    24.0,
        "Ambient_Temperature":  30.0,
        "Chiller_Usage":        65.0,
        "AHU_Usage":            40.0,
        "Cooling_Strategy_Encoded": 2,
        "Cooling_Unit_Power_Consumption_kW": 12.5,
    }

    _liquid_input = {
        "avg_P_ac":    6.0,
        "avg_P_cu":    3.5,
        "avg_T_out":   26.0,
        "avg_T_MEAS":  29.0,
        "avg_T_celCC": 32.0,
        "TLHC":        55.0,
        "DoW":         3.0,
        "WeH":         0.0,
    }

    print("\n--- predict_air() ---")
    pprint.pprint(predict_air(_air_input))

    print("\n--- predict_liquid() ---")
    pprint.pprint(predict_liquid(_liquid_input))

    print("\n--- predict_hybrid() ---")
    pprint.pprint(predict_hybrid(_air_input, _liquid_input))

    print("\n--- get_rl_state() ---")
    rl_state = get_rl_state(_air_input, _liquid_input)
    pprint.pprint(rl_state)

    print("\n--- calculate_reward() ---")
    pprint.pprint(calculate_reward(rl_state))

    print("\n--- simulate_action(action=2 → HYBRID) ---")
    pprint.pprint(simulate_action(2, _air_input, _liquid_input))

    print("\n--- ACTION AIR ---")
    pprint.pprint(simulate_action(0, _air_input, _liquid_input))

    print("\n--- ACTION LIQUID ---")
    pprint.pprint(simulate_action(1, _air_input, _liquid_input))

    print("\n--- ACTION HYBRID ---")
    pprint.pprint(simulate_action(2, _air_input, _liquid_input))

    print("\n" + "=" * 60)
    print("  Smoke test complete.")
    print("=" * 60)
