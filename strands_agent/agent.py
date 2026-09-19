"""
Strands agent wiring — explainability / ops copilot for the cooling pipeline.
Explains why an action was selected, rejected, or replaced by a fallback based
strictly on factual data logged from Digital Twin, PPO, Cedar, and metrics.
Never invents information.
"""
from __future__ import annotations

import re
import socket
from typing import Any, Dict, Optional

from strands import Agent
from strands.models.ollama import OllamaModel

from strands_agent.tools import explain_decision, query_recent_decisions
from decision_logger import get_decision

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_PORT = 11434


def is_ollama_available() -> bool:
    """Fast probe to check if Ollama server is running locally."""
    try:
        with socket.create_connection(("localhost", OLLAMA_PORT), timeout=0.2):
            return True
    except (OSError, socket.timeout):
        return False


ollama_model = OllamaModel(
    host=OLLAMA_HOST,
    model_id="llama3.1",
)

SYSTEM_PROMPT = (
    "You are an operations copilot for the Thermion data center cooling system. "
    "Your role is to explain cooling decisions grounded strictly in logged data. "
    "Always use explain_decision or query_recent_decisions. "
    "In your explanations, always cite: "
    "1. The step_id. "
    "2. The PPO proposed action and the actual telemetry metrics (temperature deviation, efficiency, water usage). "
    "3. The Cedar policy verdict (allowed or denied) and the specific reason. "
    "4. Whether a safe fallback was applied and why that fallback action was chosen. "
    "5. The final executed action. "
    "Never invent or assume numbers, policies, or decisions not found in the logged decision."
)

agent = Agent(
    model=ollama_model,
    tools=[query_recent_decisions, explain_decision],
    system_prompt=SYSTEM_PROMPT,
)


def format_factual_explanation(decision: Dict[str, Any]) -> str:
    """
    Generate a strictly grounded, non-hallucinated explanation of a decision
    directly from the logged document data.
    """
    if not decision or not decision.get("found", True):
        return f"Decision record not found: {decision.get('reason', 'No data available.')}"

    step_id = decision.get("step_id", "?")
    ppo_action = decision.get("ppo_action") or decision.get("ppo_action_label", "UNKNOWN")
    final_action = decision.get("final_action") or decision.get("final_action_label", "UNKNOWN")
    fallback_applied = decision.get("fallback_applied", False)
    fallback_reason = decision.get("fallback_reason")

    cedar = decision.get("cedar_verdict", {})
    cedar_allowed = cedar.get("allowed", False)
    cedar_reason = cedar.get("reason", "unknown")

    safety = decision.get("safety_verdict") or decision.get("safety_filter_verdict", {})
    safety_intervened = safety.get("intervention_applied", False)
    safety_reason = safety.get("reason", "none")
    risk_level = safety.get("risk_level", "LOW")

    state = decision.get("state", {})
    temp_dev = state.get("temperature_deviation", 0.0)
    cooling_eff = state.get("cooling_efficiency", 0.5)
    water_use = state.get("water_usage", 0.0)
    lot = state.get("liquid_outlet_temp", 25.0)

    metrics = decision.get("metrics", {})

    lines = [
        f"### Step {step_id} Decision Explanation",
        f"- **Proposed Action (PPO)**: {ppo_action}",
        f"- **Telemetry State**: Temperature Deviation = {temp_dev:.2f}°C, Efficiency = {cooling_eff:.2f}, Water Usage = {water_use:.2f}L, Liquid Outlet Temp = {lot:.2f}°C",
        f"- **Cedar Policy Check**: {'ALLOWED' if cedar_allowed else 'DENIED'} ({cedar_reason})",
        f"- **Safety Filter Verdict**: Risk Level = {risk_level}, Intervention = {safety_intervened} ({safety_reason})",
    ]

    if fallback_applied or not cedar_allowed or safety_intervened:
        lines.append(f"- **Fallback Applied**: YES (Action replaced: {ppo_action} -> {final_action})")
        lines.append(f"- **Fallback Reason**: {fallback_reason or cedar_reason or safety_reason}")
    else:
        lines.append(f"- **Fallback Applied**: NO (PPO proposed action {ppo_action} approved without intervention)")

    lines.append(f"- **Final Executed Action**: {final_action}")

    if metrics:
        lines.append(
            f"- **Observed Outcome**: Temperature = {metrics.get('temperature', temp_dev):.2f}°C, "
            f"Energy Savings = {metrics.get('energy', 0.0):.1f}%, Total Reward = {metrics.get('total_reward', 0.0):.2f}"
        )

    return "\n".join(lines)


def ask(question: str) -> str:
    """
    Entry point for ops queries.
    Uses Strands agent when Ollama is available; falls back to deterministic
    grounded explanation from logged data if Ollama is offline.
    """
    # 1. Try live Strands agent with Ollama if available
    if is_ollama_available():
        try:
            return str(agent(question))
        except Exception:
            pass

    # 2. Grounded deterministic fallback (extracts step_id from question)
    match = re.search(r"step\s*#?\s*(\d+)", question, re.IGNORECASE)
    if match:
        step_id = int(match.group(1))
        doc = explain_decision(step_id)
        return format_factual_explanation(doc)

    # If general question without step_id, return recent decisions summary
    recent = query_recent_decisions(3)
    if not recent:
        return "No logged decisions found. Run the cooling pipeline first."

    summaries = [format_factual_explanation(explain_decision(d.get("step_id", 0))) for d in recent]
    return "\n\n".join(summaries)


if __name__ == "__main__":
    print(ask("Explain decision for step 0"))
