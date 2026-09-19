"""
run_local.py
============
Orchestrates the complete Thermion Decision Pipeline:
  Telemetry
  → Digital Twin (XGBoost)
  → PPO Agent (AIR / LIQUID / HYBRID)
  → Cedar Safety Check
  → Approved / Fallback Action
  → Cooling Simulator / Controller
  → OpenSearch Logging
  → Strands Agent Explanation

Does NOT retrain or rewrite existing ML models.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from stable_baselines3 import PPO

import digital_twin
from cedar.cedar_check import check_action
from cooling_controller import CoolingController, APPROVED_ACTIONS
from decision_logger import build_decision_json, log_decision
from rl_agent import CoolingPPOAgent, ACTION_LABELS
from rl_environment import CoolingEnvironment
from safety_filter import SafetyFilter, SAFE_FALLBACK_ACTION
from strands_agent.agent import ask
from train_rl import DEFAULT_AIR_PARAMS, DEFAULT_LIQUID_PARAMS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(name)s — %(message)s",
)
logger = logging.getLogger("ThermionPipeline")

MODEL_PATH = "models_rl/ppo_cooling_agent.zip"
NUM_STEPS = 10


def step_pipeline(
    step_id: int,
    env: CoolingEnvironment,
    controller: CoolingController,
    agent: CoolingPPOAgent,
    sf: SafetyFilter,
    obs: Any,
) -> Dict[str, Any]:
    """
    Execute one full step of the end-to-end decision pipeline.
    """
    # 1. Telemetry (current environment state)
    current_state = dict(env._current_state)

    # 2. Digital Twin Prediction (baseline hybrid forecast before action)
    dt_forecast = digital_twin.predict_hybrid(
        env._current_air_params,
        env._current_liquid_params,
    )

    # 3. PPO Agent Proposal (AIR / LIQUID / HYBRID)
    action_raw, _ = agent.model.predict(obs, deterministic=True)
    ppo_action = int(action_raw)
    ppo_action_label = ACTION_LABELS.get(ppo_action, str(ppo_action))

    # Evaluate safety filter for risk score & violations
    approved_sf_action, safety_report = sf.validate_action(ppo_action, current_state)

    # 4. Cedar Safety Check
    cedar_allowed, cedar_reason = check_action(ppo_action_label, current_state)

    # 5. Approved or Safe Fallback Action
    fallback_applied = False
    fallback_reason: Optional[str] = None

    if not cedar_allowed:
        fallback_applied = True
        fallback_reason = f"Cedar policy rejection: {cedar_reason}"
        final_action, final_action_label = sf.select_fallback_action(
            ppo_action, current_state, reason=cedar_reason
        )
    elif safety_report["intervention_applied"]:
        fallback_applied = True
        fallback_reason = f"Safety filter intervention: {safety_report['reason']}"
        final_action = approved_sf_action
        final_action_label = safety_report["approved_action_label"]
    else:
        final_action = ppo_action
        final_action_label = ppo_action_label

    # 6. Cooling Controller / Simulator Execution
    exec_outcome = controller.execute_action(final_action)

    # 7. Decision Document & OpenSearch Logging
    strategy_rec = agent.recommend_strategy(obs, state_dict=current_state)
    strategy_reason = strategy_rec.get("rationale") if isinstance(strategy_rec, dict) else str(strategy_rec)

    decision_doc = build_decision_json(
        step_id=step_id,
        twin_result=exec_outcome["sim_result"],
        safety_report=safety_report,
        cedar_allowed=cedar_allowed,
        cedar_reason=cedar_reason,
        strategy_reason=strategy_reason,
        ppo_action=ppo_action,
        ppo_action_label=ppo_action_label,
        final_action=final_action,
        final_action_label=final_action_label,
        fallback_applied=fallback_applied,
        fallback_reason=fallback_reason,
    )
    log_decision(decision_doc)

    return {
        "step_id": step_id,
        "decision": decision_doc,
        "exec_outcome": exec_outcome,
        "next_obs": exec_outcome["obs"],
        "terminated": exec_outcome["terminated"],
        "truncated": exec_outcome["truncated"],
    }


def run(num_steps: int = NUM_STEPS) -> None:
    """Run the complete end-to-end cooling optimization loop."""
    logger.info("Initializing Thermion Cooling Pipeline...")

    # Build environment and controller
    env = CoolingEnvironment(
        air_params=DEFAULT_AIR_PARAMS,
        liquid_params=DEFAULT_LIQUID_PARAMS,
    )
    controller = CoolingController(env)

    # Load existing trained PPO model
    ppo_model = PPO.load(MODEL_PATH)
    agent = CoolingPPOAgent(env=env)
    agent.model = ppo_model

    sf = SafetyFilter()

    obs, _ = env.reset()
    logger.info("Pipeline initialized. Starting %d optimization steps...", num_steps)

    for step_id in range(num_steps):
        result = step_pipeline(step_id, env, controller, agent, sf, obs)
        obs = result["next_obs"]

        doc = result["decision"]
        logger.info(
            "Step %02d | PPO=%s | Cedar=%s | Final=%s (fallback=%s) | Reward=%.2f",
            step_id,
            doc["ppo_action_label"],
            "ALLOW" if doc["cedar_verdict"]["allowed"] else "DENY",
            doc["final_action_label"],
            doc["fallback_applied"],
            doc["metrics"]["total_reward"],
        )

        if result["terminated"] or result["truncated"]:
            logger.info("Episode finished. Resetting environment...")
            obs, _ = env.reset()

    # 8. Demonstrate Strands Agent explanation on the final step
    logger.info("Querying Strands Explainability Agent for Step 0...")
    explanation = ask("Explain decision for step 0")
    print("\n" + "=" * 60)
    print("STRANDS AGENT GROUNDED EXPLANATION:")
    print("=" * 60)
    print(explanation)
    print("=" * 60 + "\n")


def run_pipeline(num_steps: int = NUM_STEPS) -> str:
    """Entry point alias for external callers and API handlers."""
    run(num_steps)
    return f"Completed {num_steps} optimization steps successfully"


def lambda_handler(event: Any, context: Any) -> Dict[str, Any]:
    """Entry point for AWS SAM API Gateway."""
    params = (event or {}).get("queryStringParameters") or {}
    steps = int(params.get("steps", NUM_STEPS))
    msg = run_pipeline(steps)
    return {"statusCode": 200, "body": msg}


if __name__ == "__main__":
    run()
