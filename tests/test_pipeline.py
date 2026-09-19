"""
tests/test_pipeline.py
======================
Automated test suite verifying the complete Thermion decision pipeline:
  1. Safe action validation and execution (no fallback)
  2. Rejected / unsafe action handling (Cedar rejects -> safe fallback applied)
  3. Invalid action rejection (out-of-bounds action -> rejected by Cedar/Controller)
  4. Cedar failure / error handling (graceful fallback without crash)
  5. OpenSearch logging structure and retrieval
  6. Strands agent grounded explanation (accurate, non-hallucinated citations)
"""
import pytest
from unittest.mock import patch

from cedar.cedar_check import check_action
from cooling_controller import CoolingController, InvalidActionError, APPROVED_ACTIONS
from decision_logger import (
    build_decision_json,
    log_decision,
    get_decision,
    get_recent_decisions,
    _RECENT_DECISIONS_BUFFER,
)
from rl_environment import CoolingEnvironment
from safety_filter import (
    SafetyFilter,
    ACTION_AIR,
    ACTION_LIQUID,
    ACTION_HYBRID,
    SAFE_FALLBACK_ACTION,
    TEMP_DEVIATION_LIMIT,
)
from strands_agent.agent import ask, format_factual_explanation
from strands_agent.tools import explain_decision
from train_rl import DEFAULT_AIR_PARAMS, DEFAULT_LIQUID_PARAMS


@pytest.fixture
def env():
    """Build and initialize a standard test cooling environment."""
    e = CoolingEnvironment(
        air_params=DEFAULT_AIR_PARAMS,
        liquid_params=DEFAULT_LIQUID_PARAMS,
    )
    e.reset()
    return e


@pytest.fixture
def controller(env):
    """Build a cooling controller wrapping the environment."""
    return CoolingController(env)


@pytest.fixture
def safety_filter():
    """Build a safety filter instance."""
    return SafetyFilter()


# ---------------------------------------------------------------------------
# Test 1: Safe Action
# ---------------------------------------------------------------------------
def test_safe_action(controller, safety_filter):
    """
    When state is within safe operational envelope:
      - Cedar should ALLOW approved actions
      - SafetyFilter should not intervene
      - Controller executes the proposed action without fallback
    """
    safe_state = {
        "temperature_deviation": 2.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 25.0,
        "cooling_efficiency": 0.85,
    }

    # Test Cedar allows approved action
    allowed, reason = check_action("AIR", safe_state)
    assert allowed is True
    assert "within safety envelope" in reason

    # Safety filter check
    approved_action, report = safety_filter.validate_action(ACTION_AIR, safe_state)
    assert approved_action == ACTION_AIR
    assert report["intervention_applied"] is False

    # Controller execution
    outcome = controller.execute_action(ACTION_AIR)
    assert outcome["action"] == ACTION_AIR
    assert outcome["action_label"] == "AIR"
    assert "reward" in outcome
    assert outcome["reward"] > 0


# ---------------------------------------------------------------------------
# Test 2: Rejected / Unsafe Action
# ---------------------------------------------------------------------------
def test_rejected_unsafe_action(safety_filter):
    """
    When state exceeds TEMP_DEVIATION_LIMIT (6.0°C):
      - Cedar must DENY the action
      - Pipeline must trigger the existing safe fallback mechanism
      - Never execute the raw unapproved PPO action
    """
    unsafe_temp = TEMP_DEVIATION_LIMIT + 1.5  # 7.5°C > 6.0°C
    unsafe_state = {
        "temperature_deviation": unsafe_temp,
        "water_usage": 50.0,
        "liquid_outlet_temp": 25.0,
        "cooling_efficiency": 0.85,
    }

    # Cedar must reject
    allowed, reason = check_action("HYBRID", unsafe_state)
    assert allowed is False
    assert "temperature_deviation" in reason or "denied" in reason

    # Safe fallback selection: critically hot state triggers liquid cooling to quench
    fallback_action, fallback_label = safety_filter.select_fallback_action(
        proposed_action=ACTION_HYBRID,
        state=unsafe_state,
        reason=reason,
    )
    assert fallback_action == ACTION_LIQUID
    assert fallback_label == "LIQUID"


# ---------------------------------------------------------------------------
# Test 3: Invalid Action
# ---------------------------------------------------------------------------
def test_invalid_action(controller):
    """
    When an invalid action is provided:
      - Cedar must reject it (not in approved action set)
      - CoolingController must reject it with InvalidActionError
    """
    state = {
        "temperature_deviation": 2.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 25.0,
        "cooling_efficiency": 0.85,
    }

    # Cedar rejects unapproved action names
    allowed, reason = check_action("SUPER_TURBO_COOL", state)
    assert allowed is False
    assert "not in approved set" in reason or "denied" in reason

    # Controller rejects invalid action codes
    with pytest.raises(InvalidActionError):
        controller.execute_action(99)

    with pytest.raises(InvalidActionError):
        controller.execute_action("INVALID_NAME")


# ---------------------------------------------------------------------------
# Test 4: Cedar Failure / Exception Handling
# ---------------------------------------------------------------------------
def test_cedar_failure(safety_filter):
    """
    If Cedar evaluation raises an unexpected error or fails:
      - check_action should catch it and return allowed=False
      - Pipeline engages safe fallback rather than crashing
    """
    state = {
        "temperature_deviation": 2.0,
        "water_usage": 50.0,
        "liquid_outlet_temp": 25.0,
        "cooling_efficiency": 0.85,
    }

    with patch("cedar.cedar_check.is_authorized", side_effect=RuntimeError("Cedar engine timeout")):
        allowed, reason = check_action("AIR", state)
        assert allowed is False
        assert "error" in reason

        # Safe fallback engaged
        fallback_action, fallback_label = safety_filter.select_fallback_action(
            proposed_action=ACTION_AIR,
            state=state,
            reason=reason,
        )
        assert fallback_action in (ACTION_AIR, ACTION_LIQUID, ACTION_HYBRID)


# ---------------------------------------------------------------------------
# Test 5: OpenSearch Logging & Retrieval
# ---------------------------------------------------------------------------
def test_opensearch_logging():
    """
    Verify decision document contains all required fields and is retrievable.
    """
    mock_twin_result = {
        "action": 0,
        "action_label": "AIR",
        "next_state": {
            "temperature_deviation": 1.2,
            "water_usage": 30.0,
            "liquid_outlet_temp": 22.0,
            "cooling_efficiency": 0.75,
        },
        "reward_breakdown": {
            "total_reward": 4.5,
            "r_water": 3.0,
            "r_energy": 0.5,
            "r_efficiency": 1.0,
            "r_temp": 0.0,
            "r_overheating": 0.0,
        },
        "hybrid_output": {
            "outlet_temperature": 22.0,
            "energy_cost": 150.0,
            "energy_savings_percent": 12.5,
            "water_savings_percent": 25.0,
            "thermal_stability": 0.9,
        },
    }

    mock_safety_report = {
        "intervention_applied": False,
        "reason": "none",
        "risk_level": "LOW",
        "risk_score": 0.15,
        "proposed_action": 0,
        "proposed_action_label": "AIR",
    }

    doc = build_decision_json(
        step_id=999,
        twin_result=mock_twin_result,
        safety_report=mock_safety_report,
        cedar_allowed=True,
        cedar_reason="cedar: within safety envelope",
        strategy_reason="High efficiency state",
        ppo_action=0,
        ppo_action_label="AIR",
        final_action=0,
        final_action_label="AIR",
        fallback_applied=False,
    )

    # Verify all required fields from prompt
    assert doc["step_id"] == 999
    assert "state" in doc
    assert "digital_twin_prediction" in doc
    assert doc["ppo_action"] == 0
    assert doc["ppo_action_label"] == "AIR"
    assert doc["cedar_verdict"]["allowed"] is True
    assert doc["final_action"] == 0
    assert doc["final_action_label"] == "AIR"
    assert doc["fallback_applied"] is False
    assert "metrics" in doc
    assert doc["metrics"]["temperature"] == 1.2
    assert doc["metrics"]["water"] == 30.0
    assert doc["metrics"]["total_reward"] == 4.5

    # Log and retrieve
    log_decision(doc)
    retrieved = get_decision(999)
    assert retrieved is not None
    assert retrieved["step_id"] == 999


# ---------------------------------------------------------------------------
# Test 6: Strands Agent Grounded Explanation
# ---------------------------------------------------------------------------
def test_strands_agent_explanation():
    """
    Verify Strands agent retrieves decision and generates explanation citing
    actual telemetry, Cedar verdict, and fallback status without inventing data.
    """
    mock_twin_result = {
        "action": 1,
        "action_label": "LIQUID",
        "next_state": {
            "temperature_deviation": 7.2,
            "water_usage": 45.0,
            "liquid_outlet_temp": 24.0,
            "cooling_efficiency": 0.65,
        },
        "reward_breakdown": {"total_reward": 1.2},
        "hybrid_output": {},
    }

    mock_safety_report = {
        "intervention_applied": True,
        "reason": "temperature_deviation 7.20°C exceeds limit 6.0°C",
        "risk_level": "HIGH",
        "risk_score": 0.78,
    }

    doc = build_decision_json(
        step_id=888,
        twin_result=mock_twin_result,
        safety_report=mock_safety_report,
        cedar_allowed=False,
        cedar_reason="cedar: temperature_deviation 7.20°C > 6.0°C limit",
        strategy_reason="Operator override",
        ppo_action=0,
        ppo_action_label="AIR",
        final_action=1,
        final_action_label="LIQUID",
        fallback_applied=True,
        fallback_reason="Cedar policy rejection",
    )
    log_decision(doc)

    # Query explanation
    explanation = ask("Explain decision for step 888")

    # Assert factual grounding
    assert "888" in explanation
    assert "AIR" in explanation
    assert "LIQUID" in explanation
    assert "DENIED" in explanation
    assert "Fallback Applied" in explanation and "YES" in explanation
    assert "7.20" in explanation or "7.2" in explanation
