"""
Builds the JSON decision document (matching opensearch_schema.json) from a
single pipeline step's outputs, and pushes it into the local OpenSearch
index. Doesn't touch digital_twin.py / safety_filter.py / rl_agent.py —
it just consumes what they already return.
"""
import datetime
import os

from opensearchpy import OpenSearch

INDEX_NAME = "cooling-decisions"

_client = OpenSearch(
    hosts=[{
        "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
        "port": int(os.environ.get("OPENSEARCH_PORT", 9200)),
    }],
    use_ssl=False,
)


def build_decision_json(
    step_id: int,
    twin_result: dict,
    safety_report: dict,
    cedar_allowed: bool,
    cedar_reason: str,
    strategy_reason: str | None = None,
) -> dict:
    """
    twin_result: whatever digital_twin.simulate_action(...) returns —
                 {next_state, reward_breakdown, hybrid_output, action, action_label}
    safety_report: safety_filter.py's existing report object —
                 {intervention_applied, reason, risk_level, risk_score}
    strategy_reason: from rl_agent.py's recommend_strategy(), passed in
                 separately since it isn't part of simulate_action()'s return.
    """
    state = twin_result["next_state"]
    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "step_id": step_id,
        "state": {
            "temperature_deviation": state["temperature_deviation"],
            "water_usage": state["water_usage"],
            "liquid_outlet_temp": state["liquid_outlet_temp"],
            "cooling_efficiency": state["cooling_efficiency"],
        },
        "action": twin_result["action"],
        "action_label": twin_result["action_label"],
        "reward_breakdown": twin_result["reward_breakdown"],
        "strategy_reason": strategy_reason,
        "safety_filter_verdict": {
            "intervention_applied": safety_report["intervention_applied"],
            "reason": safety_report["reason"],
            "risk_level": safety_report["risk_level"],
            "risk_score": safety_report["risk_score"],
        },
        "cedar_verdict": {
            "allowed": cedar_allowed,
            "reason": cedar_reason,
        },
    }


def log_decision(decision_json: dict) -> None:
    _client.index(index=INDEX_NAME, body=decision_json)


def create_index() -> None:
    """One-time setup — run this once after docker-compose up. Also doable via curl (see README)."""
    import json
    from pathlib import Path

    schema = json.loads((Path(__file__).parent / "opensearch_schema.json").read_text())
    if not _client.indices.exists(index=INDEX_NAME):
        _client.indices.create(index=INDEX_NAME, body=schema)


if __name__ == "__main__":
    create_index()
    print(f"Index '{INDEX_NAME}' ready.")
