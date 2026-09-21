# Thermion

### AI-Driven Data Center Cooling Optimization Platform

Thermion is an AI-driven data center cooling optimization platform designed to reduce unnecessary energy and water consumption while maintaining hardware thermal safety.

Data centers continuously consume significant amounts of energy and water to keep computing infrastructure within safe temperature limits. However, cooling requirements change with workload and environmental conditions. Thermion uses AI to dynamically select an appropriate cooling strategy while placing a policy-based safety layer between the AI decision and execution.

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

## Key Features

### 1. AI-Based Cooling Optimization

Thermion uses a Digital Twin and machine learning models to understand the current thermal state of the data center.

The PPO reinforcement learning agent then proposes an appropriate cooling mode based on the current conditions.

### 2. Digital Twin

The Digital Twin models the data center's thermal and cooling behavior.

It provides predictions that are used by the reinforcement learning system before making a cooling decision.

### 3. Reinforcement Learning

A PPO-based reinforcement learning agent selects one of:

```text
AIR
LIQUID
HYBRID
```

The objective is to make cooling decisions based on the current operating conditions rather than using one fixed cooling strategy.

### 4. Safety-First AI

Thermion does not allow the AI model to directly control the cooling system.

Every proposed action is checked by Cedar before execution.

Example safety conditions include:

```text
Temperature deviation ≤ 6.0°C
Water usage ≥ 0.0 L
Cooling efficiency ∈ [0, 1]
Liquid outlet temperature ∈ [0, 80°C]
```

Only valid cooling actions are permitted.

### 5. Safety Fallback

If the proposed AI action is rejected, Thermion uses a fallback strategy instead of executing the unsafe decision.

For example, when the thermal deviation crosses the defined safety threshold, the system can reject the proposed decision and select a fallback cooling action based on the current thermal and liquid-loop conditions.

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

Thermion uses Strands Agents to provide explanations based on the actual decision data and logs.

Instead of simply saying:

> "The AI selected LIQUID."

The system can explain the decision by showing the relevant conditions, proposed action, safety verdict, fallback status, and final action.

---

# Architecture

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

# Technology Stack

## AI / Machine Learning

* Python
* XGBoost
* PPO Reinforcement Learning
* Digital Twin simulation

## AWS / AWS Open-Source Technologies

### Cedar

Used as the policy-based safety layer.

Cedar evaluates the proposed cooling action against predefined safety constraints before the action reaches the controller.

### Strands Agents

Used to build the AI explanation workflow.

The agent retrieves decision information and produces grounded explanations based on the recorded system data.

### AWS SAM CLI

Used to structure and test the serverless application locally and prepare the project for AWS-compatible deployment workflows.

### LocalStack

Used during development to simulate AWS services locally and test AWS-based workflows without requiring a full cloud deployment for every development cycle.

### Amazon PartyRock

Used to create an interactive demonstration of the AI workflow and show the different stages of the Thermion decision process.

---

# Project Structure

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

# End-to-End Workflow

A typical Thermion optimization cycle works as follows:

### Step 1 — Collect Telemetry

The system receives the current data center operating conditions.

### Step 2 — Predict Thermal Behavior

The Digital Twin uses the current state to predict the expected behavior of the cooling environment.

### Step 3 — Select Cooling Mode

The PPO agent evaluates the state and proposes:

```text
AIR
LIQUID
or
HYBRID
```

### Step 4 — Validate the Decision

The proposed action is passed to Cedar.

Cedar checks the action against the configured safety policies.

### Step 5 — Handle the Result

If Cedar allows the action:

```text
PPO Decision
      ↓
Cedar ALLOW
      ↓
Controller
```

If Cedar denies the action:

```text
PPO Decision
      ↓
Cedar DENY
      ↓
Safety Fallback
      ↓
Controller
```

### Step 6 — Execute

The approved or fallback cooling action is sent to the cooling controller.

### Step 7 — Log

The complete decision is recorded for monitoring and analysis.

### Step 8 — Explain

The Strands Agent uses the logged information to provide a human-readable explanation of the decision.

---

# Safety Design

Safety is one of the core principles of Thermion.

The AI model proposes actions, but it does not have unrestricted control over the cooling system.

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

This separation allows the optimization system and the safety system to operate independently.

The safety policy can therefore reject an AI decision even when that decision was produced by the trained reinforcement learning model.

---

# Testing

Thermion includes tests for the core decision pipeline.

Run:

```bash
pytest tests/test_pipeline.py -v
```

The test suite covers important parts of the workflow, including safety validation, fallback behavior, controller execution, and decision processing.

An unsafe scenario can also be tested by providing telemetry that crosses the configured thermal safety threshold and verifying that:

```text
Unsafe State
    ↓
PPO Proposal
    ↓
Cedar DENY
    ↓
Fallback
    ↓
Controller
    ↓
Decision Log
```

---

# Running Locally

## 1. Clone the Repository

```bash
git clone <repository-url>
cd Thermion
```

## 2. Create a Virtual Environment

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

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Run the Local Pipeline

```bash
python run_local.py
```

The local pipeline runs the complete flow from telemetry through AI decision-making, Cedar validation, fallback handling, controller execution, logging, and explanation.

---

# AWS SAM / LocalStack Development

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

# Example Decision

A normal decision may look like:

```text
Telemetry
   ↓
Digital Twin Prediction
   ↓
PPO → AIR
   ↓
Cedar → ALLOW
   ↓
Final Action → AIR
   ↓
Logged
```

An unsafe decision may look like:

```text
Telemetry
   ↓
Thermal deviation > safety limit
   ↓
PPO → Proposed Action
   ↓
Cedar → DENY
   ↓
Safety Fallback
   ↓
Final Action
   ↓
Logged + Explained
```

This demonstrates that the safety layer remains in control of what can actually be executed.

---

# Users

Thermion is designed primarily for:

### Data Center Operators

Operators can use Thermion to monitor:

* Current thermal conditions
* Cooling mode
* AI decisions
* Safety status
* Fallback interventions
* Real-time system behavior

### Data Center Managers

Managers can use the platform to understand:

* Energy usage
* Water usage
* Cooling efficiency
* Cooling strategy over time
* Safety interventions
* AI decision history

---

# Project Goals

Thermion focuses on three main goals:

### Reduce Resource Consumption

Optimize cooling decisions to reduce unnecessary energy and water consumption.

### Maintain Thermal Safety

Ensure that AI-generated cooling decisions are validated before execution.

### Make AI Decisions Understandable

Record and explain decisions so that operators can understand what happened and why.

---

# Key Idea

Thermion follows a simple principle:

> **AI should optimize the system, but safety should control what the AI is allowed to do.**

The combination of machine learning, reinforcement learning, policy-based safety, cloud tooling, and explainable AI allows Thermion to move from an AI model to a complete decision-making system.

---

# Team

Built as part of an AWS-focused hackathon project.

### Contributions

* Backend and AI pipeline
* AWS SAM CLI and LocalStack integration
* Frontend development and backend integration
* UI/UX and wireframe design
* Amazon PartyRock AI workflow demonstration

---

# Future Scope

Potential future improvements include:

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
