from dataclasses import dataclass
import logging
from typing import Dict, List, Literal, Optional
import time
import math
import time

from booster_robotics_sdk_python import (
    B1LowCmdPublisher,
    LowCmd,
    MotorCmd,
    LowCmdType,
    B1JointIndex,
    B1LowStateSubscriber,
    ChannelFactory,
    B1LocoClient,
    RobotMode,
    LowState
)

from .helpers import stringify_motor_cmds, stringify_q_values


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booster_python_client")

NUM_MOTORS = 23

KP_HARD = 80.0
KP_MED = 40.0
KP_SOFT = 20.0
KD_MED = 2.0
WEIGHT_MED = 1.0


@dataclass
class MotorCommandMaker:
    @staticmethod
    def create_neutral_motor_cmds() -> List[MotorCmd]:
        cmds = []
        for _ in range(NUM_MOTORS):
            mc = MotorCmd()
            mc.mode = 0
            mc.q = 0.0
            mc.dq = 0.0
            mc.tau = 0.0
            mc.kp = 0.0
            mc.kd = 0.0
            mc.weight = 0.0
            cmds.append(mc)
        return cmds

    @staticmethod
    def _get_pd_gains(speed: str):
        "Returns (kp, kd, weight) tuple based on speed setting"
        if speed == "fast":
            return KP_HARD, KD_MED, WEIGHT_MED
        elif speed == "medium":
            return KP_MED, KD_MED, WEIGHT_MED
        else:  # slow
            return KP_SOFT, KD_MED, WEIGHT_MED

    @staticmethod
    def set_targets_rel(
        prev_cmds: List[MotorCmd],
        cmds: List[MotorCmd],
        targets: dict[B1JointIndex, float],
        speed: Optional[Literal["fast", "medium", "slow"]] = "medium",
    ):
        """targets: dict{joint_enum: abs_angle_rad}"""
        kp, kd, weight = MotorCommandMaker._get_pd_gains(speed)
        for j, q_rel in targets.items():
            idx = int(j)
            if 0 <= idx < len(cmds):
                prev_cmds[idx].q = prev_cmds[idx].q + q_rel
                prev_cmds[idx].kp = kp
                prev_cmds[idx].kd = kd
                prev_cmds[idx].weight = weight

    @staticmethod
    def set_targets_abs(
        prev_cmds: List[MotorCmd],
        targets: dict[B1JointIndex, float],
        speed: Optional[Literal["fast", "medium", "slow"]] = "medium",
    ):
        """targets: dict{joint_enum: abs_angle_rad}"""
        kp, kd, weight = MotorCommandMaker._get_pd_gains(speed)
        for j, q_abs in targets.items():
            idx = int(j)
            prev_cmds[idx].q = q_abs
            prev_cmds[idx].kp = kp
            prev_cmds[idx].kd = kd
            prev_cmds[idx].weight = weight


def get_joint_name_by_index(index: int) -> str:
    try:
        return B1JointIndex(index).name.lower()
    except ValueError:
        return "unknown"


@dataclass
class BoosterLowLevelController:
    low_state_msg: LowState = None

    def init(self, network_domain=0, network_interface=""):
        # initialize publisher
        logger.info("Initializing BoosterLowLevelController")
        ChannelFactory.Instance().Init(
            domain_id=network_domain, network_interface=network_interface
        )  # set your domain/interface as needed
        self.pub = B1LowCmdPublisher()
        self.pub.InitChannel()
        self.sub = B1LowStateSubscriber(handler=self._grab_low_state_handler)
        self.sub.InitChannel()
        self.loco_client = B1LocoClient()
        self.loco_client.Init()

        self._motor_command_states = (
            MotorCommandMaker.create_neutral_motor_cmds()
        )  # TODO Replace with a subscriber read
        logger.info("Initialized BoosterLowLevelController")

    def close(self):
        logger.info("Closing BoosterLowLevelController")
        self.pub.CloseChannel()

    def _grab_low_state_handler(self, msg: LowState):
        self.low_state_msg = msg

    def read_latest_low_state(self, motor_indices: List[int]) -> str:
        # wait up to ~10s to get one packet
        for _ in range(1000):
            if self.low_state_msg is not None:
                break
            time.sleep(0.01)

        if self.low_state_msg is None:
            raise RuntimeError(
                "Did not receive LowState; check channels / domain / wiring"
            )

        serial_states = self.low_state_msg.motor_state_serial  # list[MotorState]
        q_values = stringify_q_values(serial_states, motor_indices)
        print(q_values)
        return q_values

    def _send_motor_cmds(self, cmds: List[MotorCmd]):
        msg = LowCmd()
        msg.cmd_type = LowCmdType.SERIAL
        msg.motor_cmd = cmds
        if not self.pub.Write(msg):
            raise RuntimeError("Publish LowCmd failed")

    def send_neutral_pose(self):
        cmds = MotorCommandMaker.create_neutral_motor_cmds()
        self._send_motor_cmds(cmds)

    def send_command(
        self,
        motor_states: List[Dict[B1JointIndex, float]],
        speed: Literal["fast", "medium", "slow"] = "medium",
        time_gap_s=1,
    ):
        "Send a list of (shoulder_pitch, shoulder_roll, elbow_pitch, elbow_yaw) tuples"

        for m_state in motor_states:
            MotorCommandMaker.set_targets_abs(
                self._motor_command_states, m_state, speed
            )
            logger.debug(
                f"Sending arm command:\n{stringify_motor_cmds(self._motor_command_states)}"
            )
            self._send_motor_cmds(self._motor_command_states)
            time.sleep(time_gap_s)

    def set_mode(self, mode: RobotMode):
        self.loco_client.ChangeMode(mode)

    def enable_arm_usage(self):
        self.loco_client.ChangeMode(RobotMode.kPrepare)
        time.sleep(4)  # wait for mode change to take effect
        self.loco_client.SwitchHandEndEffectorControlMode(True)
