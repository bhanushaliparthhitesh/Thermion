"""
Strands agent wiring — the explainability / ops copilot for the cooling
pipeline. Runs against a local Ollama model, so it needs no AWS account
and no Bedrock access (Build It track requirement).

Prereq: `ollama pull llama3.1` (or whichever model you swap in below)
and `ollama serve` running locally.
"""
from strands import Agent
from strands.models.ollama import OllamaModel

from tools import explain_decision, query_recent_decisions

ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="llama3.1",  # swap for whatever you've pulled locally
)

agent = Agent(
    model=ollama_model,
    tools=[query_recent_decisions, explain_decision],
    system_prompt=(
        "You are an operations copilot for a data center cooling system. "
        "Use query_recent_decisions and explain_decision to answer questions "
        "about what the cooling agent has done and why. Always cite the "
        "step_id and the safety/Cedar verdicts when explaining a decision. "
        "Never invent a decision you haven't fetched from OpenSearch."
    ),
)


if __name__ == "__main__":
    # Step 7's "Done when" check — ask it a real operator-style question.
    print(agent('why did you pick LIQUID at step 12?'))
