"""
decision_logger.py
==================
Builds the JSON decision document matching opensearch_schema.json from
pipeline step outputs, and pushes it to OpenSearch (or memory buffer).
"""
from __future__ import annotations

import datetime
import os
import socket
from typing import Any, Dict, List, Optional

from opensearchpy import OpenSearch

INDEX_NAME = "cooling-decisions"

_client = OpenSearch(
    hosts=[{
        "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
        "port": int(os.environ.get("OPENSEARCH_PORT", 9200)),
    }],
    use_ssl=False,
    timeout=1,
    max_retries=0,
    retry_on_timeout=False,
)

# In-memory buffer of recent decisions (accessible when OpenSearch is offline)
_RECENT_DECISIONS_BUFFER: List[Dict[str, Any]] = []
_MAX_BUFFER_SIZE = 200

_opensearch_available: Optional[bool] = None


def is_opensearch_available() -> bool:
    """Test whether OpenSearch is reachable on host:port via quick socket probe."""
    global _opensearch_available
    if _opensearch_available is None:
        host = os.environ.get("OPENSEARCH_HOST", "localhost")
        port = int(os.environ.get("OPENSEARCH_PORT", 9200))
        try:
            with socket.create_connection((host, port), timeout=0.2):
                _opensearch_available = True
        except (OSError, socket.timeout):
            _opensearch_available = False
            print(f"[INFO] OpenSearch server not reachable at {host}:{port}. Decisions will be buffered in memory. (Run `docker-compose up -d` to enable)")
    return _opensearch_available


def build_decision_json(
    step_id: int,
    twin_result: Dict[str, Any],
    safety_report: Dict[str, Any],
    cedar_allowed: bool,
    cedar_reason: str,
    strategy_reason: Optional[str] = None,
    ppo_action: Optional[int] = None,
    ppo_action_label: Optional[str] = None,
    final_action: Optional[int] = None,
    final_action_label: Optional[str] = None,
    fallback_applied: bool = False,
    fallback_reason: Optional[str] = None,
    metrics: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Build structured decision document matching opensearch_schema.json.
    """
    state = twin_result.get("next_state") or {}
    reward_bd = twin_result.get("reward_breakdown") or {}
    hybrid_out = twin_result.get("hybrid_output") or {}

    # Infer ppo action if not explicitly supplied
    if ppo_action is None:
        ppo_action = safety_report.get("proposed_action", twin_result.get("action", 0))
    if ppo_action_label is None:
        ppo_action_label = safety_report.get("proposed_action_label", twin_result.get("action_label", "AIR"))

    # Infer final action if not explicitly supplied
    if final_action is None:
        final_action = twin_result.get("action", ppo_action)
    if final_action_label is None:
        final_action_label = twin_result.get("action_label", ppo_action_label)

    def _val(d: Dict[str, Any], key: str, fallback: float) -> float:
        v = d.get(key)
        if v is None:
            return float(fallback)
        try:
            return float(v)
        except (ValueError, TypeError):
            return float(fallback)

    # Compile metrics
    temp_val = _val(state, "temperature_deviation", 0.0)
    water_val = _val(state, "water_usage", 0.0)
    eff_val = _val(state, "cooling_efficiency", 0.5)
    lot_val = _val(state, "liquid_outlet_temp", 25.0)
    risk_score_val = _val(safety_report, "risk_score", 0.0)
    tot_reward_val = _val(reward_bd, "total_reward", 0.0)

    compiled_metrics = {
        "temperature": temp_val,
        "energy": _val(hybrid_out, "energy_savings_percent", eff_val * 100.0),
        "water": water_val,
        "risk_score": risk_score_val,
        "total_reward": tot_reward_val,
    }
    if metrics:
        compiled_metrics.update(metrics)

    # Digital twin predictions
    dt_pred = {
        "outlet_temperature": _val(hybrid_out, "outlet_temperature", lot_val),
        "energy_cost": _val(hybrid_out, "energy_cost", 0.0),
        "temperature_deviation": temp_val,
        "water_usage": water_val,
        "avg_outlet_temp": lot_val,
        "thermal_stability": _val(hybrid_out, "thermal_stability", 0.8),
        "cooling_efficiency": eff_val,
        "water_savings_percent": _val(hybrid_out, "water_savings_percent", 0.0),
        "energy_savings_percent": _val(hybrid_out, "energy_savings_percent", 0.0),
    }

    doc = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "step_id": step_id,
        "state": {
            "temperature_deviation": temp_val,
            "water_usage": water_val,
            "liquid_outlet_temp": lot_val,
            "cooling_efficiency": eff_val,
        },
        "digital_twin_prediction": dt_pred,
        "ppo_action": int(ppo_action),
        "ppo_action_label": str(ppo_action_label),
        "cedar_verdict": {
            "allowed": bool(cedar_allowed),
            "reason": str(cedar_reason),
        },
        "safety_filter_verdict": {
            "intervention_applied": bool(safety_report.get("intervention_applied", False)),
            "reason": str(safety_report.get("reason", "none")),
            "risk_level": str(safety_report.get("risk_level", "LOW")),
            "risk_score": risk_score_val,
        },
        "final_action": int(final_action),
        "final_action_label": str(final_action_label),
        "fallback_applied": bool(fallback_applied),
        "fallback_reason": fallback_reason,
        "metrics": compiled_metrics,
        "reward_breakdown": reward_bd,
        "strategy_reason": strategy_reason,
        # Legacy backward-compatibility fields
        "action": str(final_action_label),
        "action_label": str(final_action_label),
    }

    return doc


def log_decision(decision_json: Dict[str, Any]) -> None:
    """Store decision in memory buffer and index to OpenSearch if reachable."""
    # 1. Always append to memory buffer (maintaining max capacity)
    _RECENT_DECISIONS_BUFFER.append(decision_json)
    if len(_RECENT_DECISIONS_BUFFER) > _MAX_BUFFER_SIZE:
        _RECENT_DECISIONS_BUFFER.pop(0)

    # 2. Push to OpenSearch if running
    if is_opensearch_available():
        try:
            _client.index(index=INDEX_NAME, body=decision_json)
        except Exception as e:
            print(f"[WARN] OpenSearch indexing error ({e}).")


def get_recent_decisions(n: int = 20) -> List[Dict[str, Any]]:
    """Return the last n logged decisions from OpenSearch, or memory buffer as fallback."""
    if is_opensearch_available():
        try:
            resp = _client.search(
                index=INDEX_NAME,
                body={"size": n, "sort": [{"timestamp": "desc"}]},
            )
            hits = [hit["_source"] for hit in resp["hits"]["hits"]]
            if hits:
                return hits
        except Exception:
            pass

    # Fallback: slice from local memory buffer (most recent first)
    return list(reversed(_RECENT_DECISIONS_BUFFER[-n:]))


def get_decision(step_id: int | str) -> Optional[Dict[str, Any]]:
    """Fetch one decision by step_id from OpenSearch, or memory buffer as fallback."""
    target_id = int(step_id)
    if is_opensearch_available():
        try:
            resp = _client.search(
                index=INDEX_NAME,
                body={"query": {"term": {"step_id": target_id}}, "size": 1},
            )
            hits = resp["hits"]["hits"]
            if hits:
                return hits[0]["_source"]
        except Exception:
            pass

    # Fallback: search memory buffer
    for doc in reversed(_RECENT_DECISIONS_BUFFER):
        if doc.get("step_id") == target_id:
            return doc
    return None


def create_index() -> None:
    """Create the OpenSearch index if it does not already exist."""
    import json
    from pathlib import Path

    schema = json.loads((Path(__file__).parent / "opensearch_schema.json").read_text(encoding="utf-8"))
    if is_opensearch_available() and not _client.indices.exists(index=INDEX_NAME):
        _client.indices.create(index=INDEX_NAME, body=schema)
        print(f"Created index {INDEX_NAME}")


if __name__ == "__main__":
    create_index()
