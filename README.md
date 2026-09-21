# Thermion

### AI-Driven Data Center Cooling Optimization Platform

<img width="1917" height="862" alt="Screenshot 2026-09-21 135022" src="https://github.com/user-attachments/assets/a5e48a21-d35b-4645-95ed-0e67778c836e" />


Thermion is an AI-driven data center cooling optimization platform designed to reduce unnecessary energy and water consumption while maintaining hardware thermal safety.

Data centers continuously consume significant amounts of energy and water to keep computing infrastructure within safe temperature limits. However, cooling requirements change with workload and environmental conditions. Thermion uses AI to dynamically select an appropriate cooling strategy while placing a policy-based safety layer between the AI decision and execution.

**Live demo:** [Try Thermion on PartyRock →](https://partyrock.aws/u/Parthbhanushali06/K5sMpExtq/Thermion-AI-Data-Center-Cooling-Demo)

---

## Problem

Data center cooling is critical for maintaining hardware reliability, but it is also a major consumer of energy and water.

Traditional cooling strategies may not continuously adapt to changing workload and thermal conditions. This can result in cooling resources being used even when the actual cooling requirement changes.

The challenge is therefore:

> How can we dynamically optimize data center cooling while ensuring that an AI system never directly executes an unsafe cooling decision?

Thermion addresses this by combining machine learning, reinforcement learning, policy-based safety validation, and explainable AI into one pipeline.

---

## What Thermion Does

Thermion continuously processes data center telemetry and follows this workflow:

```text
Telemetry
    ↓
Digital Twin
    ↓
PPO Reinforcement Learning
    ↓
Cedar Safety Validation
    ↓
Approved / Fallback Action
    ↓
Cooling Controller
    ↓
Decision Logging
    ↓
Strands AI Explanation
```

The system can select between three cooling modes:

* AIR
* LIQUID
* HYBRID

The selected action is not executed immediately. It first passes through the safety layer.

If the decision satisfies the defined safety policies, it is approved.

If the decision violates a safety constraint, it is rejected and Thermion activates a fallback strategy.

---

## Live Dashboard

<img width="1310" height="722" alt="Screenshot 2026-09-21 135040" src="https://github.com/user-attachments/assets/a403b3c1-f380-4fd8-a396-05bb3191285f" />


The dashboard surfaces the core live state of the system at a glance: Facility PUE, hot-aisle temperature, the current approved cooling mode, and a running Cedar Safety Guard violation counter. Below that sits a real-time zone heatmap of the facility alongside a plain-language rationale for the most recent decision — including confidence, predicted savings, and latency — backed by an immutable, hash-verified decision ledger.

---

## The Pipeline

 <img width="1882" height="772" alt="Screenshot 2026-09-21 135330" src="https://github.com/user-attachments/assets/2bf906c4-046c-4515-b6aa-f65c2759b82d" />

Every optimization cycle runs the same strictly deterministic, five-step sequence, continuously, every 30 seconds:

1. **Sensor data** — multi-zone thermistors, rack delta-T, outdoor wet-bulb temperature, and power draw telemetry ingested at high rate.
2. **AI predicts** — the Digital Twin forward-models thermal drift over the next 15-minute horizon using XGBoost surrogates.
3. **RL recommends** — the PPO policy evaluates the state space and selects AIR, LIQUID, or HYBRID with targeted pump RPM and flow rate.
4. **Safety verifies** — Cedar's mathematical boundary checks validate thermodynamic thresholds before dispatch; unsafe commands are blocked with zero tolerance.
5. **Logged & told** — every decision is appended to an immutable OpenSearch ledger and synthesized into human-readable rationale for operations staff.

---

## Key Features

### 1. AI-Based Cooling Optimization

Thermion uses a Digital Twin and machine learning models to understand the current thermal state of the data center. The PPO reinforcement learning agent then proposes an appropriate cooling mode based on the current conditions.

### 2. Digital Twin

The Digital Twin models the data center's thermal and cooling behavior. It provides predictions that are used by the reinforcement learning system before making a cooling decision.

### 3. Reinforcement Learning

A PPO-based reinforcement learning agent selects one of `AIR`, `LIQUID`, or `HYBRID`. The objective is to make cooling decisions based on the current operating conditions rather than using one fixed cooling strategy.

### 4. Safety-First AI

Thermion does not allow the AI model to directly control the cooling system. Every proposed action is checked by Cedar before execution.

Example safety conditions include:

```text
Temperature deviation ≤ 6.0°C
Water usage ≥ 0.0 L
Cooling efficiency ∈ [0, 1]
Liquid outlet temperature ∈ [0, 80°C]
```

Only valid cooling actions are permitted.

### 5. Safety Fallback

If the proposed AI action is rejected, Thermion uses a fallback strategy instead of executing the unsafe decision. For example, when the thermal deviation crosses the defined safety threshold, the system can reject the proposed decision and select a fallback cooling action based on the current thermal and liquid-loop conditions.

### 6. Decision Logging

Each cooling decision is recorded with information such as:

* Current state
* Digital Twin prediction
* PPO proposed action
* Cedar verdict
* Safety filter verdict
* Final action
* Fallback status
* Cooling metrics
* Reward information

This makes the decision pipeline traceable and auditable.

### 7. AI Decision Explanation

Thermion uses Strands Agents to provide explanations based on the actual decision data and logs. Instead of simply saying "the AI selected LIQUID," the system explains the decision by showing the relevant conditions, proposed action, safety verdict, fallback status, and final action.

---

## Architecture

```text
                    ┌──────────────────┐
                    │     Telemetry    │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Digital Twin   │
                    │     XGBoost      │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │       PPO        │
                    │ Reinforcement    │
                    │    Learning      │
                    └────────┬─────────┘
                             │
                       Proposed Action
                             │
                             ▼
                    ┌──────────────────┐
                    │      Cedar       │
                    │ Safety Policies  │
                    └────────┬─────────┘
                             │
                   ┌─────────┴─────────┐
                   │                   │
                ALLOWED              DENIED
                   │                   │
                   │                   ▼
                   │            ┌─────────────┐
                   │            │   Safety    │
                   │            │   Fallback  │
                   │            └──────┬──────┘
                   │                   │
                   └─────────┬─────────┘
                             ▼
                    ┌──────────────────┐
                    │ Cooling Controller│
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Decision Logger  │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Strands Agent    │
                    │  Explanation     │
                    └──────────────────┘
```

---

## Technology Stack

### AI / Machine Learning

* Python
* XGBoost
* PPO Reinforcement Learning
* Digital Twin simulation

### AWS / AWS Open-Source Technologies

**Cedar** — used as the policy-based safety layer. Cedar evaluates the proposed cooling action against predefined safety constraints before the action reaches the controller.

**Strands Agents** — used to build the AI explanation workflow. The agent retrieves decision information and produces grounded explanations based on the recorded system data.

**AWS SAM CLI** — used to structure and test the serverless application locally and prepare the project for AWS-compatible deployment workflows.

**LocalStack** — used during development to simulate AWS services locally and test AWS-based workflows without requiring a full cloud deployment for every development cycle.

**Amazon PartyRock** — used to create an interactive demonstration of the AI workflow and show the different stages of the Thermion decision process.

---

## PartyRock Demo

 <img width="1648" height="863" alt="Screenshot 2026-09-21 140927" src="https://github.com/user-attachments/assets/58038d96-41c6-48c5-b0fe-022540d67291" />

Alongside the full local AWS stack, Thermion has a lightweight, zero-setup demonstration built on **Amazon PartyRock**. It recreates the same decision sequence — telemetry, prediction, decision, safety check, and explanation — as a chained set of generative widgets, so anyone can explore how Thermion thinks without running any code locally.

Describe a scenario using **Primary Concern** and **Severity Level**, and the app generates realistic sensor telemetry, a cooling decision, a Cedar safety verdict, and a plain-English explanation — live, in the browser.

**Try it here:** [https://partyrock.aws/u/Parthbhanushali06/K5sMpExtq/Thermion-AI-Data-Center-Cooling-Demo](https://partyrock.aws/u/Parthbhanushali06/K5sMpExtq/Thermion-AI-Data-Center-Cooling-Demo)

---

## Project Structure

```text
Thermion/
│
├── digital_twin.py
├── rl_agent.py
├── safety_filter.py
├── cooling_controller.py
├── decision_logger.py
├── export_decisions.py
├── run_local.py
│
├── models_rl/
│   └── ppo_cooling_agent.zip
│
├── cedar/
│   ├── cedar_policy.cedar
│   └── cedar_check.py
│
├── strands_agent/
│   ├── agent.py
│   └── tools.py
│
├── tests/
│   └── test_pipeline.py
│
├── opensearch_schema.json
├── pytest.ini
├── template.yaml
└── README.md
```

---

## End-to-End Workflow

A typical Thermion optimization cycle works as follows:

**Step 1 — Collect Telemetry.** The system receives the current data center operating conditions.

**Step 2 — Predict Thermal Behavior.** The Digital Twin uses the current state to predict the expected behavior of the cooling environment.

**Step 3 — Select Cooling Mode.** The PPO agent evaluates the state and proposes `AIR`, `LIQUID`, or `HYBRID`.

**Step 4 — Validate the Decision.** The proposed action is passed to Cedar, which checks the action against the configured safety policies.

**Step 5 — Handle the Result.**

If Cedar allows the action:

```text
PPO Decision → Cedar ALLOW → Controller
```

If Cedar denies the action:

```text
PPO Decision → Cedar DENY → Safety Fallback → Controller
```

**Step 6 — Execute.** The approved or fallback cooling action is sent to the cooling controller.

**Step 7 — Log.** The complete decision is recorded for monitoring and analysis.

**Step 8 — Explain.** The Strands Agent uses the logged information to provide a human-readable explanation of the decision.

---

## Safety Design

Safety is one of the core principles of Thermion. The AI model proposes actions, but it does not have unrestricted control over the cooling system.

The decision flow is:

```text
AI proposes
     ↓
Safety policy checks
     ↓
Safe?
 ┌───┴───┐
YES      NO
 │        │
 ▼        ▼
Execute  Fallback
```

This separation allows the optimization system and the safety system to operate independently. The safety policy can therefore reject an AI decision even when that decision was produced by the trained reinforcement learning model.

---

## Testing

Thermion includes tests for the core decision pipeline.

```bash
pytest tests/test_pipeline.py -v
```

The test suite covers important parts of the workflow, including safety validation, fallback behavior, controller execution, and decision processing. An unsafe scenario can also be tested by providing telemetry that crosses the configured thermal safety threshold and verifying that:

```text
Unsafe State → PPO Proposal → Cedar DENY → Fallback → Controller → Decision Log
```

---

## Running Locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Thermion
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Local Pipeline

```bash
python run_local.py
```

The local pipeline runs the complete flow from telemetry through AI decision-making, Cedar validation, fallback handling, controller execution, logging, and explanation.

---

## AWS SAM / LocalStack Development

Thermion can also be developed and tested using AWS SAM CLI and LocalStack.

Build the SAM application:

```bash
sam build
```

Run the application locally:

```bash
sam local start-api
```

LocalStack can be used to provide a local AWS-compatible environment for development and testing.

---

## Example Decision

A normal decision may look like:

```text
Telemetry → Digital Twin Prediction → PPO → AIR → Cedar → ALLOW → Final Action → AIR → Logged
```

An unsafe decision may look like:

```text
Telemetry → Thermal deviation > safety limit → PPO → Proposed Action → Cedar → DENY → Safety Fallback → Final Action → Logged + Explained
```

This demonstrates that the safety layer remains in control of what can actually be executed.

---

## Users

### Data Center Operators

Operators can use Thermion to monitor current thermal conditions, cooling mode, AI decisions, safety status, fallback interventions, and real-time system behavior.

### Data Center Managers

Managers can use the platform to understand energy usage, water usage, cooling efficiency, cooling strategy over time, safety interventions, and AI decision history.

---

## Project Goals

**Reduce Resource Consumption** — optimize cooling decisions to reduce unnecessary energy and water consumption.

**Maintain Thermal Safety** — ensure that AI-generated cooling decisions are validated before execution.

**Make AI Decisions Understandable** — record and explain decisions so that operators can understand what happened and why.

---

## Key Idea

Thermion follows a simple principle:

> **AI should optimize the system, but safety should control what the AI is allowed to do.**

The combination of machine learning, reinforcement learning, policy-based safety, cloud tooling, and explainable AI allows Thermion to move from an AI model to a complete decision-making system.

---

## Team

Built as part of an AWS-focused hackathon project.

**Contributions:**

* Backend and AI pipeline
* AWS SAM CLI and LocalStack integration
* Frontend development and backend integration
* UI/UX and wireframe design
* Amazon PartyRock AI workflow demonstration

---

## Future Scope

* Real-time data center telemetry integration
* Deployment on AWS infrastructure
* More advanced Digital Twin modeling
* Additional cooling strategies
* Historical optimization analytics
* Advanced operator alerts
* Larger-scale multi-rack simulation
* Improved real-time 3D visualization
* Automated cost and resource optimization

---

## Thermion

**Smarter cooling. Safer decisions. More efficient data centers.**
