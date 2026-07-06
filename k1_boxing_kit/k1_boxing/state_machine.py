"""Fight-mode state machine driven by the Booster remote controller.

Transitions only (nothing runs continuously in a state). Adapted from
KyleAlanJeffrey/booster: fight mode now enables balance-safe upper-body control
on start and returns to the guard stance on stop.

Remote mapping (Booster remote):
    RT -> right punch      RB -> right uppercut     LT -> left punch
    A  -> toggle block     B  -> victory pose
"""

from enum import Enum
import logging
import threading
from typing import Dict, List

from . import actions
from .lib import BoosterLowLevelController
from .helpers import SpeedType

logger = logging.getLogger("k1_boxing")

# Remote controller event codes (from the SDK / KyleAlanJeffrey/booster).
EVENT_BTN_DN = 0x603


class RobotEvent(Enum):
    LEFT_PUNCH = "left_punch"
    RIGHT_PUNCH = "right_punch"
    RIGHT_UPPERCUT = "right_uppercut"
    BLOCK = "block"
    VICTORY_POSE = "victory_pose"


class RobotState(Enum):
    FIGHT_STANCE = "fight_stance"
    BLOCK_STANCE = "block_stance"


class FightingStateMachine:
    def __init__(
        self,
        booster: BoosterLowLevelController,
        speed: SpeedType = "slow",
        time_gap_s: float = 0.05,
        enable_motion: bool = True,
        already_standing: bool = False,
    ):
        self.booster = booster
        self.speed = speed
        self.time_gap_s = time_gap_s
        self.state = RobotState.FIGHT_STANCE
        # Ensures only one move runs at a time (drops overlapping button presses).
        self._action_lock = threading.Lock()
        # Track every candidate button for rising-edge detection (press = False->True).
        names = {n for buttons, _ in self._BUTTON_EVENTS for n in buttons}
        self._prev = {n: False for n in names}

        if enable_motion:
            # Legs stay balanced (kWalking); only the arms become custom-controlled.
            self.booster.enable_upper_body_usage(already_standing=already_standing)
            logger.info("Assuming guard stance...")
            self.booster.send_command(
                [actions.FIGHT_STANCE], speed=self.speed, time_gap_s=0.2
            )

    def _action(
        self,
        frames: List[Dict[int, float]],
        speed: SpeedType = None,
        time_gap_s: float = None,
    ) -> None:
        try:
            self.booster.send_command(
                frames,
                speed=speed or self.speed,
                time_gap_s=time_gap_s or self.time_gap_s,
            )
        except Exception as exc:
            logger.error("Action failed: %s", exc)

    def on_event(self, event: RobotEvent) -> None:
        # Stateless: every move works at any time and returns to the guard stance.
        if event == RobotEvent.LEFT_PUNCH:
            self._action(actions.LEFT_PUNCH)
        elif event == RobotEvent.RIGHT_PUNCH:
            self._action(actions.RIGHT_PUNCH)
        elif event == RobotEvent.RIGHT_UPPERCUT:
            self._action(actions.RIGHT_UPPERCUT)
        elif event == RobotEvent.BLOCK:
            # Momentary block: raise guard, then drop back to fight stance.
            self._action(actions.FIGHT_POSE_TO_BLOCK)
            self._action(actions.BLOCK_TO_FIGHT_POSE)
        elif event == RobotEvent.VICTORY_POSE:
            self._action(actions.VICTORY_ANIMATION, "slow", 0.2)

    # Each move can be triggered by ANY of several buttons (checked in this order).
    # NOTE: on the Booster remote the triggers/bumpers (rt/lt/rb) often DON'T register
    # as buttons, so each move also has a face-button / D-pad fallback that does work.
    _BUTTON_EVENTS = (
        (("rt", "y"), RobotEvent.RIGHT_PUNCH),       # Y (or RT)
        (("lt", "x"), RobotEvent.LEFT_PUNCH),        # X (or LT)
        (("rb", "b"), RobotEvent.RIGHT_UPPERCUT),    # B (or RB)
        (("a",), RobotEvent.BLOCK),                  # A
        (("hat_u", "start"), RobotEvent.VICTORY_POSE),  # D-pad up
    )

    def on_remote(self, rc) -> None:
        """Fire a move on each button PRESS (rising edge).

        We detect edges ourselves instead of trusting one specific event code, so it
        works regardless of how the remote reports events. Runs in the SDK callback
        thread, so it must never raise.
        """
        try:
            # Read current states defensively (missing attrs -> False).
            cur = {name: bool(getattr(rc, name, False)) for name in self._prev}
            newly_pressed = {n for n in cur if cur[n] and not self._prev[n]}
            self._prev = cur

            if not newly_pressed:
                return
            # Drop presses that arrive while a move is still playing.
            if not self._action_lock.acquire(blocking=False):
                return
            try:
                for buttons, event in self._BUTTON_EVENTS:
                    if newly_pressed.intersection(buttons):
                        self.on_event(event)
                        break
            finally:
                self._action_lock.release()
        except Exception as exc:
            logger.error("Remote handler error (ignored): %s", exc)

    def return_to_guard(self) -> None:
        """Best-effort return to the neutral fight stance."""
        try:
            self.booster.send_command(
                [actions.FIGHT_STANCE], speed="slow", time_gap_s=0.2
            )
        except Exception as exc:
            logger.error("Return-to-guard failed: %s", exc)
