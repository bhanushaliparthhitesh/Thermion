# Thermion — Transparent & Auditable Data Center Cooling Optimization

Thermion is an AI-powered, safety-first platform for optimizing data center cooling. It combines physics-informed Digital Twin simulation, Reinforcement Learning (PPO), formal authorization policy checks (Cedar), physical guardrails, OpenSearch audit logging, and grounded LLM explainability (Strands Agent).

Every cooling decision is **validated, verified against hard physical limits, logged to an auditable store, and explained with grounded factual metrics**.

---

## Architecture & Data Flow

```text
               ┌───────────────────────┐
               │   Sensor Telemetry    │
               │ (Temp, Water, Power)  │
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │     Digital Twin      │
               │  (XGBoost Simulation) │
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │       PPO Agent       │
               │ (AIR / LIQUID/ HYBRID)│
               └──────────┬────────────┘
                          │ Proposed Action
                          ▼
               ┌───────────────────────┐
               │  Cedar Policy Check   │
               │   & Safety Filter     │
               └──────────┬────────────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
     [Passes Envelope]           [Fails / Error]
            │                           │
            ▼                           ▼
    ┌───────────────┐           ┌───────────────┐
    │Approved Action│           │ Safe Fallback │
    │ (PPO Action)  │           │(LIQUID / AIR) │
    └───────┬───────┘           └───────┬───────┘
            │                           │
            └─────────────┬─────────────┘
                          │ Approved/Fallback Action
                          ▼
               ┌───────────────────────┐
               │  Cooling Controller   │
               │(Validates & Dispatches│
               │ to Physical Plant/Env)│
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │  OpenSearch Logging   │
               │ (Auditable Decision   │
               │   Record Indexed)     │
               └──────────┬────────────┘
                          │
                          ▼
               ┌───────────────────────┐
               │     Strands Agent     │
               │ (Grounded Explanation │
               │   of Every Action)    │
               └───────────────────────┘
```

---

## Core Components

| Component | File(s) | Description |
| :--- | :--- | :--- |
| **Telemetry & Digital Twin** | [`digital_twin.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/digital_twin.py), [`preprocess.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/preprocess.py) | Predicts thermal response, power consumption, and water usage under varying cooling regimes with realistic bounds. |
| **PPO Agent** | [`rl_agent.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/rl_agent.py), [`models_rl/`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/models_rl/) | Policy network trained to maximize energy and water savings while keeping temperatures within target thresholds. |
| **Cedar Safety Check** | [`cedar/cedar_policy.cedar`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/cedar/cedar_policy.cedar), [`cedar/cedar_check.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/cedar/cedar_check.py) | Declarative authorization policies enforcing hard operational constraints (`temp_deviation ≤ 6.0°C`, `water_usage ≥ 0.0L`, `liquid_outlet_temp ≤ 80.0°C`). |
| **Safe Fallback** | [`safety_filter.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/safety_filter.py) | When Cedar or safety checks deny an action or fail, automatically engages the safest available fallback (e.g. `LIQUID` for thermal emergencies, `AIR` when liquid loop is hot). |
| **Cooling Controller** | [`cooling_controller.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/cooling_controller.py) | Strictly enforces that only approved actions (`AIR`, `LIQUID`, `HYBRID`) are dispatched to the simulator or physical plant, blocking invalid action inputs. |
| **OpenSearch Logging** | [`decision_logger.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/decision_logger.py), [`opensearch_schema.json`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/opensearch_schema.json) | Indexes telemetry, proposed action, Cedar verdict, fallback status, final action, rewards, and risk scores. Includes an in-memory fallback buffer when OpenSearch is offline. |
| **Strands Agent** | [`strands_agent/agent.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/strands_agent/agent.py), [`strands_agent/tools.py`](file:///C:/Users/Hetvi/Documents/GitHub/Thermion/strands_agent/tools.py) | Operator copilot tool retrieving logged decisions to explain *why* an action was selected, rejected, or replaced with a fallback without hallucinating. |

---

## Getting Started

### 1. Requirements & Installation

Python 3.10+ is supported. Install dependencies:
```bash
pip install -r requirements.txt
pip install cedarpy pytest strands
```

### 2. Run the End-to-End Decision Pipeline

Run the local pipeline loop:
```bash
python run_local.py
```
This initializes the cooling environment, predicts actions using the PPO model, validates each action against Cedar, applies safe fallback if needed, dispatches approved actions to the controller, logs each step, and outputs an explanation from the Strands Agent.

### 3. Run Automated Tests

The test suite validates safe actions, unsafe action rejection, invalid action rejection, Cedar runtime failure handling, logging structure, and explanation accuracy:
```bash
pytest tests/test_pipeline.py -v
```

---

## Optional Services

### Local OpenSearch (Docker)
To index decisions into a live OpenSearch cluster:
```bash
docker-compose up -d
```
Initialize the index schema:
```bash
python decision_logger.py
```
*(If OpenSearch is not running, Thermion automatically buffers decisions in memory so tests and local runs execute without errors).*

### Local Ollama LLM (Strands Agent)
To run the live conversational copilot with local LLM inference:
```bash
ollama pull llama3.1
ollama serve
```
Test asking the agent directly:
```bash
python -c "from strands_agent.agent import ask; print(ask('Explain decision for step 0'))"
```
*(If Ollama is not running, the Strands agent automatically falls back to a deterministic, non-hallucinated explanation formatted directly from the decision telemetry).*

### Export Decisions
Export recent decisions into a markdown report:
```bash
python export_decisions.py --limit 30 --output decisions_export.md
```
