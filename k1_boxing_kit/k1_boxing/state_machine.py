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
    ):
        self.booster = booster
        self.speed = speed
        self.time_gap_s = time_gap_s
        self.state = RobotState.FIGHT_STANCE
        # Ensures only one move runs at a time (drops overlapping button presses).
        self._action_lock = threading.Lock()

        if enable_motion:
            # Legs stay balanced (kWalking); only the arms become custom-controlled.
            self.booster.enable_upper_body_usage()
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
        if self.state == RobotState.FIGHT_STANCE:
            if event == RobotEvent.BLOCK:
                self._action(actions.FIGHT_POSE_TO_BLOCK)
                self.state = RobotState.BLOCK_STANCE
            elif event == RobotEvent.LEFT_PUNCH:
                self._action(actions.LEFT_PUNCH)
            elif event == RobotEvent.RIGHT_PUNCH:
                self._action(actions.RIGHT_PUNCH)
            elif event == RobotEvent.RIGHT_UPPERCUT:
                self._action(actions.RIGHT_UPPERCUT)
            elif event == RobotEvent.VICTORY_POSE:
                self._action(actions.VICTORY_ANIMATION, "slow", 0.2)
            else:
                logger.info("Can't %s while fighting!", event.value)

        elif self.state == RobotState.BLOCK_STANCE:
            if event == RobotEvent.BLOCK:
                self._action(actions.BLOCK_TO_FIGHT_POSE)
                self.state = RobotState.FIGHT_STANCE
            elif event == RobotEvent.VICTORY_POSE:
                self._action(actions.VICTORY_ANIMATION, "slow", 0.2)
            else:
                logger.info("Can't %s while blocking!", event.value)

    def on_remote(self, rc) -> None:
        """Map remote button-down edges to fight events (one move at a time)."""
        if rc.event != EVENT_BTN_DN:
            return
        # Drop presses that arrive while a move is still playing.
        if not self._action_lock.acquire(blocking=False):
            logger.info("Busy with a move - ignoring input")
            return
        try:
            if rc.rt:
                self.on_event(RobotEvent.RIGHT_PUNCH)
            elif rc.rb:
                self.on_event(RobotEvent.RIGHT_UPPERCUT)
            elif rc.lt:
                self.on_event(RobotEvent.LEFT_PUNCH)
            elif rc.a:
                self.on_event(RobotEvent.BLOCK)
            elif rc.b:
                self.on_event(RobotEvent.VICTORY_POSE)
        finally:
            self._action_lock.release()

    def return_to_guard(self) -> None:
        """Best-effort return to the neutral fight stance."""
        try:
            if self.state == RobotState.BLOCK_STANCE:
                self._action(actions.BLOCK_TO_FIGHT_POSE)
                self.state = RobotState.FIGHT_STANCE
            self.booster.send_command(
                [actions.FIGHT_STANCE], speed="slow", time_gap_s=0.2
            )
        except Exception as exc:
            logger.error("Return-to-guard failed: %s", exc)
