"""
Orchestrator loop — wires the existing pipeline (digital_twin, safety_filter,
rl_agent) together with the new Cedar check and OpenSearch logging.

Doesn't modify preprocess.py / digital_twin.py / rl_environment.py /
rl_agent.py / train_rl.py / safety_filter.py / models/ / models_rl/ —
this file only calls into them.

The three lines marked TODO are the only parts that depend on details this
guide doesn't specify (your RL library's load call and your env class
name) — fill those in from your actual rl_agent.py / rl_environment.py.
"""
import digital_twin
import safety_filter
import rl_agent
from cedar.cedar_check import check_action
from decision_logger import build_decision_json, log_decision

MODEL_PATH = "models_rl/ppo_cooling_agent.zip"
NUM_STEPS = 30

SAFE_FALLBACK_ACTION = None  # TODO: point this at safety_filter.py's existing fallback action


def run(num_steps: int = NUM_STEPS) -> None:
    # TODO: replace with however train_rl.py actually loads the PPO model,
    # e.g. `from stable_baselines3 import PPO; model = PPO.load(MODEL_PATH)`
    raise NotImplementedError("wire in your model-loading call from train_rl.py here")
    model = ...

    # TODO: replace with your actual Gymnasium env class from rl_environment.py
    env = ...
    obs, _ = env.reset()

    for step_id in range(num_steps):
        action = model.predict(obs, deterministic=True)  # from PPO agent

        approved_action, safety_report = safety_filter.validate_action(action, obs)  # existing

        cedar_allowed, cedar_reason = check_action(approved_action["action_label"], obs)  # new

        final_action = approved_action if cedar_allowed else SAFE_FALLBACK_ACTION

        twin_result = digital_twin.simulate_action(final_action, obs)  # existing
        strategy_reason = rl_agent.recommend_strategy(obs)  # existing

        decision = build_decision_json(
            step_id, twin_result, safety_report, cedar_allowed, cedar_reason, strategy_reason
        )  # Step 3 helper
        log_decision(decision)  # Step 5

        obs, reward, terminated, truncated, info = env.step(final_action)  # keep env buffer consistent
        if terminated or truncated:
            obs, _ = env.reset()

    print(f"Logged {num_steps} decisions to OpenSearch.")


def lambda_handler(event, context):
    """Entry point for `sam local start-api` (see template.yaml)."""
    params = (event or {}).get("queryStringParameters") or {}
    steps = int(params.get("steps", NUM_STEPS))
    run(steps)
    return {"statusCode": 200, "body": f"ran {steps} steps"}


if __name__ == "__main__":
    run()
