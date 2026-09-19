"""
Thin wrapper around cedarpy that evaluates a proposed cooling action
against cedar_policy.cedar. Same shape as SafetyFilter.validate_action,
so run_local.py can treat both checks the same way:

    check_action(action_label, state) -> (allowed: bool, reason: str)
"""
from pathlib import Path
import logging

from cedarpy import Decision, is_authorized

logger = logging.getLogger("CedarCheck")

_POLICY_PATH = Path(__file__).parent / "cedar_policy.cedar"
_SCALE = 100  # keep in sync with cedar_policy.cedar's scaling comment

# Cache policy text
_CACHED_POLICY: str | None = None


def _load_policy() -> str:
    global _CACHED_POLICY
    if _CACHED_POLICY is None:
        _CACHED_POLICY = _POLICY_PATH.read_text(encoding="utf-8")
    return _CACHED_POLICY


def check_action(action_label: str, state: dict) -> tuple[bool, str]:
    """
    Validate proposed action against formal Cedar safety policies.

    Parameters
    ----------
    action_label: "AIR" | "LIQUID" | "HYBRID" (or invalid action string)
    state: dict containing temperature_deviation, water_usage,
           liquid_outlet_temp, cooling_efficiency.

    Returns
    -------
    (allowed: bool, reason: str)
    """
    try:
        policies = _load_policy()

        # Extract values with safe defaults matching physical bounds
        temp_dev = float(state.get("temperature_deviation", 0.0))
        water_use = float(state.get("water_usage", 0.0))
        cooling_eff = float(state.get("cooling_efficiency", 0.5))
        liq_outlet = float(state.get("liquid_outlet_temp", 25.0))

        request = {
            "principal": 'Agent::"rl_policy"',
            "action": f'Action::"apply_{action_label}"',
            "resource": 'System::"cooling"',
            "context": {
                "temperature_deviation_scaled": round(temp_dev * _SCALE),
                "water_usage_scaled": round(water_use * _SCALE),
                "cooling_efficiency_scaled": round(cooling_eff * _SCALE),
                "liquid_outlet_temp_scaled": round(liq_outlet * _SCALE),
            },
        }
        entities: list = []

        result = is_authorized(request, policies, entities)

        if result.decision == Decision.Allow:
            return True, "cedar: within safety envelope"

        # Determine diagnostic reason
        reasons = []
        if temp_dev > 6.0:
            reasons.append(f"temperature_deviation {temp_dev:.2f}°C > 6.0°C limit")
        if water_use < 0.0:
            reasons.append(f"water_usage {water_use:.2f}L < 0.0L min")
        if cooling_eff < 0.0 or cooling_eff > 1.0:
            reasons.append(f"cooling_efficiency {cooling_eff:.2f} outside [0.0, 1.0]")
        if liq_outlet < 0.0 or liq_outlet > 80.0:
            reasons.append(f"liquid_outlet_temp {liq_outlet:.2f}°C outside [0.0, 80.0°C]")
        if action_label not in ("AIR", "LIQUID", "HYBRID"):
            reasons.append(f"action '{action_label}' is not in approved set [AIR, LIQUID, HYBRID]")

        detailed_reason = "; ".join(reasons) if reasons else f"denied action={action_label}"
        return False, f"cedar: {detailed_reason}"

    except Exception as e:
        logger.error("Cedar policy check failed with error: %s", e)
        return False, f"cedar: error ({type(e).__name__}: {e})"


if __name__ == "__main__":
    safe_state = {
        "temperature_deviation": 2.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 18.0,
        "cooling_efficiency": 0.8,
    }
    unsafe_state = {
        "temperature_deviation": 9.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 18.0,
        "cooling_efficiency": 0.8,
    }
    invalid_action_state = {
        "temperature_deviation": 2.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 18.0,
        "cooling_efficiency": 0.8,
    }
    print("safe state ->", check_action("HYBRID", safe_state))
    print("unsafe state ->", check_action("HYBRID", unsafe_state))
    print("invalid action ->", check_action("INVALID_TURBO", invalid_action_state))
