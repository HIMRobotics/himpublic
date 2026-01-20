from enum import Enum
import logging
from typing import Dict, List, Any
from .types import SpeedType
from . import actions
from .lib import BoosterLowLevelController
from booster_robotics_sdk_python import B1JointIndex
from booster_robotics_sdk_python import RemoteControllerState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booster_python_client")

EVENT_AXIS, EVENT_HAT, EVENT_BTN_DN, EVENT_BTN_UP, EVENT_REMOVE = (
    0x600,
    0x602,
    0x603,
    0x604,
    0x606,
)


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
    """This state machine works on transitions. So there's nothing running coninuously while in a state."""

    def __init__(
        self,
        booster: BoosterLowLevelController,
        speed: SpeedType = "medium",
        time_gap_s: float = 0.05,
    ):
        self.booster = booster
        self.speed = speed
        self.time_gap_s = time_gap_s
        self.state = RobotState.FIGHT_STANCE

    def _action(
        self,
        action: List[Dict[B1JointIndex, float]],
        speed: SpeedType = None,
        time_gap_s: float = None,
    ):
        if speed and time_gap_s:
            self.booster.send_command(action, speed=speed, time_gap_s=time_gap_s)
            return
        self.booster.send_command(action, speed=self.speed, time_gap_s=self.time_gap_s)

    def on_event(self, event: RobotEvent):

        ######### Fighting state #########
        if self.state == RobotState.FIGHT_STANCE:
            # Switch to block stance
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
                logger.info(f"Cant {event.value} while fighting!")

        ######### Blocking state #########
        elif self.state == RobotState.BLOCK_STANCE:
            # Switch back to fight stance
            if event == RobotEvent.BLOCK:
                self._action(actions.BLOCK_TO_FIGHT_POSE)
                self.state = RobotState.FIGHT_STANCE
            elif event == RobotEvent.VICTORY_POSE:
                self._action(actions.VICTORY_ANIMATION)
            else:
                logger.info(f"Can't {event.value} while blocking!")

    def on_remote(self, rc: RemoteControllerState):
        """Remote controller handler. This maps buttons to edges."""
        ev = rc.event
        if ev == EVENT_BTN_DN:
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


class CameraStateEvent(Enum):
    TAKE_PICTURE = "take_picture"
    SWITCH_MODE = "switch_mode"


class CameraState(Enum):
    SCANNING = "scanning"
    FRAMING = "framing"


class CameraStateMachine:
    """"""

    def __init__(
        self,
        booster: BoosterLowLevelController,
        fingerbot: Any,
        speed: SpeedType = "slow",
        time_gap_s: float = 0.05,
    ):
        from .fingerbot import FingerBot

        self.booster = booster
        self.fingerbot: FingerBot = fingerbot
        self.speed = speed
        self.time_gap_s = time_gap_s
        self.state = CameraState.SCANNING

    def _action(
        self,
        action: List[Dict[B1JointIndex, float]],
        speed: SpeedType = None,
        time_gap_s: float = None,
    ):
        if speed and time_gap_s:
            self.booster.send_command(action, speed=speed, time_gap_s=time_gap_s)
            return
        self.booster.send_command(action, speed=self.speed, time_gap_s=self.time_gap_s)

    def tick(self):
        if self.state == CameraState.SCANNING:
            pass
        elif self.state == CameraState.FRAMING:
            pass

    def on_event(self, event: CameraStateEvent):
        ######### Scanning state #########
        if self.state == CameraState.SCANNING:
            if event == CameraStateEvent.SWITCH_MODE:
                self.state = CameraState.FRAMING
                self._action(actions.CAMERA_NEUTRAL_TO_TAKING_PHOTO)

        ######### Framing state #########
        elif self.state == CameraState.FRAMING:
            if event == CameraStateEvent.SWITCH_MODE:
                self.state = CameraState.SCANNING
                self._action(actions.TAKING_PHOTO_TO_CAMERA_NEUTRAL)
            elif event == CameraStateEvent.TAKE_PICTURE:
                self.fingerbot.finger()

    def on_remote(self, rc: RemoteControllerState):
        """Remote controller handler. This maps buttons to edges."""
        logger.info(f"RC State: {rc}")
        ev = rc.event
        if ev == EVENT_BTN_DN:
            if rc.rb:
                logger.info("Taking picture!")
                self.on_event(CameraStateEvent.TAKE_PICTURE)
            elif rc.a:
                self.on_event(CameraStateEvent.SWITCH_MODE)
