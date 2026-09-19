"""
cooling_controller.py
=====================
Executes approved cooling actions on the Cooling Environment / Digital Twin Simulator.

Guarantees:
  - Only approved actions (AIR=0, LIQUID=1, HYBRID=2) are ever dispatched to hardware/simulator.
  - Rejects any invalid action with a descriptive error.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple, Union

import digital_twin
from rl_environment import ACTION_LABELS, CoolingEnvironment

logger = logging.getLogger("CoolingController")

APPROVED_ACTIONS: Dict[int, str] = {0: "AIR", 1: "LIQUID", 2: "HYBRID"}
APPROVED_LABELS: Dict[str, int] = {v: k for k, v in APPROVED_ACTIONS.items()}


class InvalidActionError(ValueError):
    """Raised when an unapproved or out-of-bounds action is sent to the cooling controller."""
    pass


class CoolingController:
    """
    Cooling Controller / Simulator interface.

    Responsible for safely dispatching approved cooling actions
    (AIR, LIQUID, HYBRID) to the underlying environment and digital twin.
    """

    def __init__(self, env: CoolingEnvironment) -> None:
        self.env = env
        self.last_action: Optional[int] = None
        self.last_action_label: Optional[str] = None
        self.execution_count: int = 0

    def validate_action(self, action: Union[int, str]) -> Tuple[int, str]:
        """
        Validate that the action belongs to the approved cooling action set.

        Returns (action_int, action_label).
        Raises InvalidActionError if unapproved.
        """
        if isinstance(action, str):
            norm = action.strip().upper()
            if norm not in APPROVED_LABELS:
                raise InvalidActionError(
                    f"Action '{action}' is not an approved cooling action. "
                    f"Approved actions are: {list(APPROVED_LABELS.keys())}"
                )
            action_int = APPROVED_LABELS[norm]
            action_label = norm
        elif isinstance(action, (int, float)):
            action_int = int(action)
            if action_int not in APPROVED_ACTIONS:
                raise InvalidActionError(
                    f"Action code {action!r} is not an approved cooling action. "
                    f"Approved action codes are: {list(APPROVED_ACTIONS.keys())} "
                    f"({list(APPROVED_ACTIONS.values())})"
                )
            action_label = APPROVED_ACTIONS[action_int]
        else:
            raise InvalidActionError(
                f"Action of type {type(action).__name__} is invalid: {action!r}. "
                f"Must be one of {list(APPROVED_ACTIONS.values())}."
            )

        return action_int, action_label

    def execute_action(
        self,
        action: Union[int, str],
    ) -> Dict[str, Any]:
        """
        Execute an approved action on the environment and digital twin.

        Parameters
        ----------
        action : int | str
            Must be one of 0 ("AIR"), 1 ("LIQUID"), 2 ("HYBRID").

        Returns
        -------
        dict containing execution results, next state, reward, and simulation output.
        """
        action_int, action_label = self.validate_action(action)

        # 1. Step the physical / digital twin cooling environment
        obs, reward, terminated, truncated, info = self.env.step(action_int)

        # 2. Query digital twin simulation for detailed physics outputs
        sim_result = digital_twin.simulate_action(
            action=action_int,
            air_params=self.env._current_air_params,
            liquid_params=self.env._current_liquid_params,
            previous_state=self.env._previous_state,
        )

        self.last_action = action_int
        self.last_action_label = action_label
        self.execution_count += 1

        logger.info(
            "Controller executed action %s (code=%d) | reward=%.4f",
            action_label, action_int, reward
        )

        return {
            "action": action_int,
            "action_label": action_label,
            "obs": obs,
            "reward": float(reward),
            "terminated": bool(terminated),
            "truncated": bool(truncated),
            "info": info,
            "sim_result": sim_result,
            "next_state": self.env._current_state,
        }
