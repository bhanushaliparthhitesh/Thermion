"""
Thin wrapper around cedarpy that evaluates a proposed cooling action
against cedar_policy.cedar. Same shape as SafetyFilter.validate_action,
so run_local.py can treat both checks the same way:

    check_action(action_label, state) -> (allowed: bool, reason: str)
"""
from pathlib import Path

from cedarpy import Decision, is_authorized

_POLICY_PATH = Path(__file__).parent / "cedar_policy.cedar"
_SCALE = 100  # keep in sync with cedar_policy.cedar's scaling comment


def _load_policy() -> str:
    return _POLICY_PATH.read_text()


def check_action(action_label: str, state: dict) -> tuple[bool, str]:
    """
    action_label: "AIR" | "LIQUID" | "HYBRID" (from digital_twin.py / rl_agent.py)
    state: the same state dict digital_twin.simulate_action() and
           SafetyFilter.validate_action() already receive — expected to
           contain temperature_deviation, water_usage, liquid_outlet_temp,
           cooling_efficiency.
    """
    policies = _load_policy()
    request = {
        "principal": 'Agent::"rl_policy"',
        "action": f'Action::"apply_{action_label}"',
        "resource": 'System::"cooling"',
        "context": {
            "temperature_deviation_scaled": round(state["temperature_deviation"] * _SCALE),
            "water_usage_scaled": round(state["water_usage"] * _SCALE),
            "cooling_efficiency_scaled": round(state["cooling_efficiency"] * _SCALE),
        },
    }
    entities: list = []  # no entity hierarchy needed for this check

    result = is_authorized(request, policies, entities)

    if result.decision == Decision.Allow:
        return True, "cedar: within safety envelope"

    # AuthzResult also exposes .diagnostics with the policy IDs that fired.
    # Run `print(vars(result))` once against your installed cedarpy version
    # to see the exact shape, then enrich this reason string if you want
    # per-rule detail (e.g. "denied by temperature_deviation rule").
    return False, f"cedar: denied action={action_label}"


if __name__ == "__main__":
    # Step 4's "Done when" check — two hand-crafted test cases.
    safe_state = {
        "temperature_deviation": 2.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 18.0,
        "cooling_efficiency": 0.8,
    }
    unsafe_state = {
        "temperature_deviation": 9.0,  # exceeds the 6.0 limit
        "water_usage": 50.0,
        "liquid_outlet_temp": 18.0,
        "cooling_efficiency": 0.8,
    }
    print("safe state ->", check_action("HYBRID", safe_state))
    print("unsafe state ->", check_action("HYBRID", unsafe_state))
