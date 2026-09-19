"""
safety_filter.py
================
AI-Powered Data Center Cooling Optimization Platform
Stage 3A — Safety Filter

Responsibilities:
 - Validate RL actions before they are executed in the Digital Twin
 - Block or replace actions that would lead to unsafe states
 - Evaluate risk levels and return structured intervention reports
 - Act as a stateless guard layer between the RL agent and the environment

Design decisions:
 - Stateless by design: every call is independent, no internal episode state
 - Returns structured dicts so the dashboard can visualize safety events
 - "Safe fallback" strategy: when an action is blocked, the filter selects
   the safest known alternative rather than simply refusing
 - All thresholds are named constants — no magic numbers

Author: Stage 3A generation
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("SafetyFilter")

# ---------------------------------------------------------------------------
# Safety thresholds — centralised constants, no magic numbers
# ---------------------------------------------------------------------------

# Temperature deviation above which the state is considered unsafe (°C)
TEMP_DEVIATION_LIMIT: float = 6.0

# Minimum permissible cooling efficiency (normalised 0–1 from Digital Twin)
COOLING_EFFICIENCY_MIN: float = 0.0

# Minimum permissible water usage (L); negative is physically impossible
WATER_USAGE_MIN: float = 0.0

# Minimum permissible liquid outlet temperature (°C)
LIQUID_OUTLET_TEMP_MIN: float = 0.0

# Maximum permissible liquid outlet temperature (°C) — hardware protection
LIQUID_OUTLET_TEMP_MAX: float = 80.0

# Risk level thresholds (based on temperature deviation normalised to limit)
RISK_LOW_THRESHOLD: float = 0.40       # < 40 % of limit → LOW
RISK_MEDIUM_THRESHOLD: float = 0.70    # 40–70 % → MEDIUM
RISK_HIGH_THRESHOLD: float = 0.90     # 70–90 % → HIGH  (>90 % → CRITICAL)

# Action integer constants (mirrors Digital Twin / RL environment)
ACTION_AIR: int = 0
ACTION_LIQUID: int = 1
ACTION_HYBRID: int = 2

# Human-readable action labels
_ACTION_LABELS: Dict[int, str] = {
    ACTION_AIR: "AIR",
    ACTION_LIQUID: "LIQUID",
    ACTION_HYBRID: "HYBRID",
}

# Default "safest" action — air cooling is the most conservative fallback
SAFE_FALLBACK_ACTION: int = ACTION_AIR


# ---------------------------------------------------------------------------
# SafetyFilter
# ---------------------------------------------------------------------------

class SafetyFilter:
    """
    Stateless guard layer that validates RL actions against safety constraints.

    Usage
    -----
    >>> sf = SafetyFilter()
    >>> safe_action, report = sf.validate_action(proposed_action=1, state=rl_state)
    >>> if report["intervention_applied"]:
    ...     logger.warning("Safety intervention: %s", report["reason"])

    All public methods return JSON-serialisable dicts so results can be
    forwarded directly to the dashboard API.
    """

    def __init__(
        self,
        temp_deviation_limit: float = TEMP_DEVIATION_LIMIT,
        cooling_efficiency_min: float = COOLING_EFFICIENCY_MIN,
        water_usage_min: float = WATER_USAGE_MIN,
        liquid_outlet_temp_min: float = LIQUID_OUTLET_TEMP_MIN,
        liquid_outlet_temp_max: float = LIQUID_OUTLET_TEMP_MAX,
    ) -> None:
        """
        Initialise with configurable thresholds.

        All thresholds have sensible defaults derived from the project
        architecture document; override for unit testing or tuning.
        """
        self.temp_deviation_limit = temp_deviation_limit
        self.cooling_efficiency_min = cooling_efficiency_min
        self.water_usage_min = water_usage_min
        self.liquid_outlet_temp_min = liquid_outlet_temp_min
        self.liquid_outlet_temp_max = liquid_outlet_temp_max

        logger.info(
            "SafetyFilter initialised — temp_limit=%.1f°C, eff_min=%.2f, "
            "water_min=%.1f L, outlet=[%.1f, %.1f]°C",
            self.temp_deviation_limit,
            self.cooling_efficiency_min,
            self.water_usage_min,
            self.liquid_outlet_temp_min,
            self.liquid_outlet_temp_max,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_action(
        self,
        proposed_action: int,
        state: Dict[str, float],
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Validate a proposed RL action against the current state.

        If the current state is already unsafe, the action is replaced with
        the safe fallback regardless of what was proposed.  If the state is
        safe, the proposed action is returned unchanged.

        Parameters
        ----------
        proposed_action : int
            Action integer from the RL agent (0=AIR, 1=LIQUID, 2=HYBRID).
        state : dict
            RL state dict as returned by ``digital_twin.get_rl_state()``.
            Expected keys: temperature_deviation, water_usage,
            liquid_outlet_temp, cooling_efficiency.

        Returns
        -------
        (approved_action, intervention_report)
            approved_action  : int    — the action that should be executed
            intervention_report : dict — structured safety report for logging
                                         and dashboard display
        """
        if proposed_action not in _ACTION_LABELS:
            raise ValueError(
                f"Invalid action {proposed_action!r}. "
                f"Must be one of {list(_ACTION_LABELS)}."
            )

        violations = self._collect_violations(state)
        risk = self.evaluate_risk(state)

        if violations:
            approved_action = self._choose_safe_alternative(
                proposed_action, violations, state
            )
            intervention_applied = True
            reason = "; ".join(violations)
            logger.warning(
                "Safety intervention: action %s → %s | %s",
                _ACTION_LABELS[proposed_action],
                _ACTION_LABELS[approved_action],
                reason,
            )
        else:
            approved_action = proposed_action
            intervention_applied = False
            reason = "none"

        report: Dict[str, Any] = {
            "proposed_action":       proposed_action,
            "proposed_action_label": _ACTION_LABELS[proposed_action],
            "approved_action":       approved_action,
            "approved_action_label": _ACTION_LABELS[approved_action],
            "intervention_applied":  intervention_applied,
            "reason":                reason,
            "violations":            violations,
            "risk_level":            risk["risk_level"],
            "risk_score":            risk["risk_score"],
        }

        return approved_action, report

    # ------------------------------------------------------------------

    def apply_constraints(
        self, state: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Apply hard physical constraints to a state dict.

        Clamps values to their valid operating ranges and flags any fields
        that required correction.  This is a pure transformation — it does
        not modify the original dict.

        Parameters
        ----------
        state : dict
            RL state dict (from ``get_rl_state()``).

        Returns
        -------
        dict with keys:
            constrained_state : dict   — state after clamping
            corrections       : list   — list of field names that were clamped
            any_corrected     : bool
        """
        constrained: Dict[str, float] = {}
        corrections: List[str] = []

        # temperature_deviation — must be non-negative
        td = state.get("temperature_deviation", 0.0)
        if _is_nan_or_inf(td) or td < 0.0:
            constrained["temperature_deviation"] = 0.0
            corrections.append("temperature_deviation")
        else:
            constrained["temperature_deviation"] = td

        # water_usage — must be >= WATER_USAGE_MIN
        wu = state.get("water_usage", 0.0)
        if _is_nan_or_inf(wu) or wu < self.water_usage_min:
            constrained["water_usage"] = self.water_usage_min
            corrections.append("water_usage")
        else:
            constrained["water_usage"] = wu

        # liquid_outlet_temp — must be in [min, max]
        lot = state.get("liquid_outlet_temp", 25.0)
        if _is_nan_or_inf(lot):
            constrained["liquid_outlet_temp"] = 25.0   # safe neutral
            corrections.append("liquid_outlet_temp")
        elif lot < self.liquid_outlet_temp_min:
            constrained["liquid_outlet_temp"] = self.liquid_outlet_temp_min
            corrections.append("liquid_outlet_temp")
        elif lot > self.liquid_outlet_temp_max:
            constrained["liquid_outlet_temp"] = self.liquid_outlet_temp_max
            corrections.append("liquid_outlet_temp")
        else:
            constrained["liquid_outlet_temp"] = lot

        # cooling_efficiency — must be >= COOLING_EFFICIENCY_MIN
        ce = state.get("cooling_efficiency", 0.5)
        if _is_nan_or_inf(ce) or ce < self.cooling_efficiency_min:
            constrained["cooling_efficiency"] = self.cooling_efficiency_min
            corrections.append("cooling_efficiency")
        else:
            constrained["cooling_efficiency"] = ce

        return {
            "constrained_state": constrained,
            "corrections":       corrections,
            "any_corrected":     bool(corrections),
        }

    # ------------------------------------------------------------------

    def is_safe_state(self, state: Dict[str, float]) -> bool:
        """
        Return True if the state passes all safety checks.

        This is a fast boolean check; use ``validate_action`` or
        ``_collect_violations`` for the full structured report.

        Parameters
        ----------
        state : dict
            RL state dict (from ``get_rl_state()``).

        Returns
        -------
        bool
        """
        return len(self._collect_violations(state)) == 0

    # ------------------------------------------------------------------

    def evaluate_risk(self, state: Dict[str, float]) -> Dict[str, Any]:
        """
        Compute a continuous risk score and categorical risk level.

        Risk is driven primarily by temperature deviation (the most
        safety-critical metric).  NaN / Inf states are treated as CRITICAL.

        Parameters
        ----------
        state : dict
            RL state dict (from ``get_rl_state()``).

        Returns
        -------
        dict with keys:
            risk_score : float   — 0.0 (safe) to 1.0+ (critical)
            risk_level : str     — "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
            details    : dict    — per-metric risk contributions
        """
        td  = state.get("temperature_deviation", 0.0)
        wu  = state.get("water_usage", 0.0)
        ce  = state.get("cooling_efficiency", 0.5)
        lot = state.get("liquid_outlet_temp", 25.0)

        # NaN / Inf → immediate CRITICAL
        if any(_is_nan_or_inf(v) for v in [td, wu, ce, lot]):
            return {
                "risk_score": 1.0,
                "risk_level": "CRITICAL",
                "details": {
                    "nan_or_inf_detected": True,
                    "temp_risk": 1.0,
                    "efficiency_risk": 1.0,
                    "water_risk": 1.0,
                    "outlet_risk": 1.0,
                },
            }

        # Temperature risk: linear from 0 → 1 as td goes from 0 → limit
        temp_risk = min(td / (self.temp_deviation_limit + 1e-9), 1.0)

        # Efficiency risk: inverse — low efficiency = high risk
        eff_risk = max(0.0, 1.0 - ce)

        # Water usage risk: very high water_usage indicates overloaded system
        # Normalise against a 1000 L operational ceiling
        water_risk = min(wu / 1000.0, 1.0)

        # Outlet temperature risk: normalise against hardware max
        outlet_range = self.liquid_outlet_temp_max - self.liquid_outlet_temp_min
        outlet_risk = min(
            max(lot - self.liquid_outlet_temp_min, 0.0) / (outlet_range + 1e-9),
            1.0,
        )

        # Weighted composite — temperature is the dominant signal (0.55)
        risk_score = (
            0.55 * temp_risk
            + 0.20 * eff_risk
            + 0.15 * water_risk
            + 0.10 * outlet_risk
        )

        risk_level = _score_to_risk_level(risk_score)

        return {
            "risk_score": round(risk_score, 4),
            "risk_level": risk_level,
            "details": {
                "nan_or_inf_detected": False,
                "temp_risk":    round(temp_risk, 4),
                "efficiency_risk": round(eff_risk, 4),
                "water_risk":   round(water_risk, 4),
                "outlet_risk":  round(outlet_risk, 4),
            },
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_violations(self, state: Dict[str, float]) -> List[str]:
        """
        Return a list of human-readable violation strings.
        Empty list means the state is safe.
        """
        violations: List[str] = []

        td  = state.get("temperature_deviation", 0.0)
        wu  = state.get("water_usage", 0.0)
        ce  = state.get("cooling_efficiency", 0.5)
        lot = state.get("liquid_outlet_temp", 25.0)

        # NaN / Inf checks — must be first
        nan_fields = [
            k for k, v in state.items() if _is_nan_or_inf(v)
        ]
        if nan_fields:
            violations.append(f"NaN/Inf detected in fields: {nan_fields}")
            # No further checks make sense if numerics are invalid
            return violations

        if td > self.temp_deviation_limit:
            violations.append(
                f"temperature_deviation={td:.2f}°C exceeds limit "
                f"{self.temp_deviation_limit}°C"
            )

        if ce < self.cooling_efficiency_min:
            violations.append(
                f"cooling_efficiency={ce:.4f} below minimum "
                f"{self.cooling_efficiency_min}"
            )

        if wu < self.water_usage_min:
            violations.append(
                f"water_usage={wu:.2f} L below minimum {self.water_usage_min} L"
            )

        if lot < self.liquid_outlet_temp_min:
            violations.append(
                f"liquid_outlet_temp={lot:.2f}°C below minimum "
                f"{self.liquid_outlet_temp_min}°C"
            )
        elif lot > self.liquid_outlet_temp_max:
            violations.append(
                f"liquid_outlet_temp={lot:.2f}°C exceeds maximum "
                f"{self.liquid_outlet_temp_max}°C"
            )

        return violations

    def _choose_safe_alternative(
        self,
        proposed_action: int,
        violations: List[str],
        state: Dict[str, float],
    ) -> int:
        """
        Select the safest available action given current violations.

        Heuristic:
          - If temperature is critically high → prefer LIQUID (best heat removal)
          - If liquid outlet temp is high → prefer AIR (avoids liquid system)
          - Otherwise → fall back to SAFE_FALLBACK_ACTION (AIR)
        """
        td  = state.get("temperature_deviation", 0.0)
        lot = state.get("liquid_outlet_temp", 25.0)

        # High temperature → liquid cooling removes heat most effectively
        if td > self.temp_deviation_limit and lot < self.liquid_outlet_temp_max * 0.8:
            return ACTION_LIQUID

        # Liquid system itself is running hot → use air only
        if lot > self.liquid_outlet_temp_max * 0.8:
            return ACTION_AIR

        return SAFE_FALLBACK_ACTION


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _is_nan_or_inf(value: Any) -> bool:
    """Return True if value is NaN, Inf, or not a finite float."""
    try:
        return not math.isfinite(float(value))
    except (TypeError, ValueError):
        return True


def _score_to_risk_level(score: float) -> str:
    """Map a 0–1 risk score to a categorical level."""
    if score < RISK_LOW_THRESHOLD:
        return "LOW"
    if score < RISK_MEDIUM_THRESHOLD:
        return "MEDIUM"
    if score < RISK_HIGH_THRESHOLD:
        return "HIGH"
    return "CRITICAL"


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pprint

    sf = SafetyFilter()

    safe_state = {
        "temperature_deviation": 2.0,
        "water_usage": 300.0,
        "liquid_outlet_temp": 28.0,
        "cooling_efficiency": 0.75,
    }

    unsafe_state = {
        "temperature_deviation": 7.5,   # over limit
        "water_usage": 300.0,
        "liquid_outlet_temp": 28.0,
        "cooling_efficiency": 0.75,
    }

    nan_state = {
        "temperature_deviation": float("nan"),
        "water_usage": 300.0,
        "liquid_outlet_temp": 28.0,
        "cooling_efficiency": 0.75,
    }

    print("\n=== Safe state, action=LIQUID ===")
    action, report = sf.validate_action(1, safe_state)
    pprint.pprint(report)

    print("\n=== Unsafe state (overheating), action=AIR ===")
    action, report = sf.validate_action(0, unsafe_state)
    pprint.pprint(report)

    print("\n=== NaN state, action=HYBRID ===")
    action, report = sf.validate_action(2, nan_state)
    pprint.pprint(report)

    print("\n=== apply_constraints on unsafe state ===")
    pprint.pprint(sf.apply_constraints(unsafe_state))

    print("\n=== evaluate_risk on safe state ===")
    pprint.pprint(sf.evaluate_risk(safe_state))
