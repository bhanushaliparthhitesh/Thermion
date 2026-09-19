"""
Strands tool functions for the ops/explainability agent.
Tools read logged decisions from OpenSearch (or decision_logger buffer).
Never invents decisions or touches the ML model directly.
"""
from __future__ import annotations

from typing import Any, Dict, List
from strands import tool

from decision_logger import get_decision, get_recent_decisions


@tool
def query_recent_decisions(n: int = 5) -> List[Dict[str, Any]]:
    """Return the last n logged cooling decisions, most recent first."""
    return get_recent_decisions(n)


@tool
def explain_decision(step_id: int) -> Dict[str, Any]:
    """
    Fetch one decision by step_id and return its complete factual details
    including state, PPO proposed action, Cedar verdict, final executed action,
    fallback status, and physical metrics.
    """
    doc = get_decision(step_id)
    if not doc:
        return {"found": False, "reason": f"No logged decision found for step {step_id}"}

    return {
        "found": True,
        "step_id": doc.get("step_id", step_id),
        "state": doc.get("state", {}),
        "digital_twin_prediction": doc.get("digital_twin_prediction", {}),
        "ppo_action": doc.get("ppo_action_label") or doc.get("action_label", "UNKNOWN"),
        "final_action": doc.get("final_action_label") or doc.get("action_label", "UNKNOWN"),
        "fallback_applied": doc.get("fallback_applied", False),
        "fallback_reason": doc.get("fallback_reason"),
        "cedar_verdict": doc.get("cedar_verdict", {}),
        "safety_verdict": doc.get("safety_filter_verdict", {}),
        "metrics": doc.get("metrics", {}),
        "reward_breakdown": doc.get("reward_breakdown", {}),
        "strategy_reason": doc.get("strategy_reason"),
    }
