"""HTTP handlers used by AWS SAM local API Gateway routes.

These handlers intentionally keep the HTTP layer thin. Replace the TODO imports/
integration points only if your existing pipeline exposes different function names.
"""
import json
import os
from typing import Any

from decision_logger import get_recent_decisions, get_decision

def _response(status_code: int, body: Any):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }

def run(event, context):
    """POST /run

    Calls the local orchestrator. Replace the import/function below if your
    run_local.py uses a different entry point.
    """
    try:
        from run_local import run_pipeline
        result = run_pipeline()
        return _response(200, {"ok": True, "result": result})
    except Exception as exc:
        return _response(500, {"ok": False, "error": str(exc)})

def get_decisions(event, context):
    """GET /decisions?limit=20"""
    try:
        params = event.get("queryStringParameters") or {}
        limit = int(params.get("limit", "20"))
        limit = max(1, min(limit, 100))
        decisions = get_recent_decisions(limit)
        return _response(200, {"ok": True, "decisions": decisions})
    except Exception as exc:
        return _response(500, {"ok": False, "error": str(exc)})

def get_decision_detail(event, context):
    """GET /decisions/{step_id}"""
    try:
        step_id = (event.get("pathParameters") or {}).get("step_id")
        if not step_id:
            return _response(400, {"ok": False, "error": "step_id is required"})

        decision = get_decision(step_id)
        if decision is None:
            return _response(404, {"ok": False, "error": "Decision not found"})
        return _response(200, {"ok": True, "decision": decision})
    except Exception as exc:
        return _response(500, {"ok": False, "error": str(exc)})

def ask_agent(event, context):
    """POST /agent/ask with JSON body: {"question": "..."}"""
    try:
        body = json.loads(event.get("body") or "{}")
        question = str(body.get("question", "")).strip()
        if not question:
            return _response(400, {"ok": False, "error": "question is required"})

        from strands_agent.agent import ask
        answer = ask(question)
        return _response(200, {"ok": True, "answer": answer})
    except Exception as exc:
        return _response(500, {"ok": False, "error": str(exc)})

def options(event, context):
    return _response(204, {})
