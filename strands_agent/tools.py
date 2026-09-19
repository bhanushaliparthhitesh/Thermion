"""
Strands tool functions for the ops/explainability agent. Both tools only
read from OpenSearch — they never touch the ML pipeline or the model
directly, so the agent can't act outside what's already been logged.
"""
import os

from opensearchpy import OpenSearch
from strands import tool

INDEX_NAME = "cooling-decisions"

_client = OpenSearch(
    hosts=[{
        "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
        "port": int(os.environ.get("OPENSEARCH_PORT", 9200)),
    }],
    use_ssl=False,
)


@tool
def query_recent_decisions(n: int = 5) -> list[dict]:
    """Return the last n logged cooling decisions, most recent first."""
    resp = _client.search(
        index=INDEX_NAME,
        body={"size": n, "sort": [{"timestamp": "desc"}]},
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]


@tool
def explain_decision(step_id: int) -> dict:
    """Fetch one decision by step_id and return its strategy plus safety/Cedar verdicts."""
    resp = _client.search(
        index=INDEX_NAME,
        body={"query": {"term": {"step_id": step_id}}, "size": 1},
    )
    hits = resp["hits"]["hits"]
    if not hits:
        return {"found": False, "reason": f"no logged decision for step {step_id}"}

    doc = hits[0]["_source"]
    return {
        "found": True,
        "step_id": step_id,
        "action_label": doc["action_label"],
        "strategy_reason": doc.get("strategy_reason"),
        "safety_verdict": doc["safety_filter_verdict"],
        "cedar_verdict": doc["cedar_verdict"],
    }
