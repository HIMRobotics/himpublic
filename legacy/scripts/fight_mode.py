from dataclasses import dataclass
import logging
from typing import Dict, List, Literal, Optional, Tuple
import time
import math
import signal
import threading
import time

from booster_robotics_sdk_python import (
    B1LowCmdPublisher,
    LowCmd,
    MotorCmd,
    LowCmdType,
    B1JointIndex,
    B1LowStateSubscriber,
    ChannelFactory,
    MotorState,
    B1LocoClient,
    RobotMode,
    B1RemoteControllerStateSubscriber,
    RemoteControllerState,
)

DEG_TO_RAD = math.pi / 180.0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BoosterLowLevelController")

NUM_MOTORS = 23

KP_HARD = 80.0
KP_MED = 40.0
KP_SOFT = 20.0
KD_MED = 2.0
WEIGHT_MED = 1.0

ARM_JOINTS_RIGHT = [
    B1JointIndex.kRightShoulderPitch,  # forward/back
    B1JointIndex.kRightShoulderRoll,  # lateral
    B1JointIndex.kRightElbowPitch,  # extend/flex
    B1JointIndex.kRightElbowYaw,
]

ARM_JOINTS_LEFT = [
    B1JointIndex.kLeftShoulderPitch,  # forward/back
    B1JointIndex.kLeftShoulderRoll,  # lateral
    B1JointIndex.kLeftElbowPitch,  # extend/flex
    B1JointIndex.kLeftElbowYaw,
]

RIGHT_ARM_TORSO_JOINTS_INDICES = [
    int(B1JointIndex.kRightShoulderPitch),  # forward/back
    int(B1JointIndex.kRightShoulderRoll),  # lateral
    int(B1JointIndex.kRightElbowPitch),  # extend/flex
    int(B1JointIndex.kRightElbowYaw),
    int(B1JointIndex.kWaist),  # twist
]

LEFT_ARM_TORSO_JOINTS_INDICES = [
    int(B1JointIndex.kLeftShoulderPitch),  # forward/back
    int(B1JointIndex.kLeftShoulderRoll),  # lateral
    int(B1JointIndex.kLeftElbowPitch),  # extend/flex
    int(B1JointIndex.kLeftElbowYaw),
    int(B1JointIndex.kWaist),  # twist
]

LEFT_RIGHT_ARM_TORSO_JOINTS_INDICES = [
    int(B1JointIndex.kLeftShoulderPitch),  # forward/back
    int(B1JointIndex.kLeftShoulderRoll),  # lateral
    int(B1JointIndex.kLeftElbowPitch),  # extend/flex
    int(B1JointIndex.kLeftElbowYaw),
    int(B1JointIndex.kRightShoulderPitch),  # forward/back
    int(B1JointIndex.kRightShoulderRoll),  # lateral
    int(B1JointIndex.kRightElbowPitch),  # extend/flex
    int(B1JointIndex.kRightElbowYaw),
]


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


def tuple_to_joint_dict(
    joint_indices: List[B1JointIndex], values: Tuple[float, ...]
) -> Dict[B1JointIndex, float]:
    if len(joint_indices) != len(values):
        raise ValueError("Length of joint_indices and values must match")
    return {joint_indices[i]: values[i] for i in range(len(joint_indices))}


def stringify_motor_cmds(cmds: List[MotorCmd]) -> str:
    s = ""
    for i, cmd in enumerate(cmds):
        s += f"  Motor {i}: mode={cmd.mode}, q={cmd.q:.2f}, dq={cmd.dq:.2f}, tau={cmd.tau:.2f}, kp={cmd.kp:.1f}, kd={cmd.kd:.1f}, weight={cmd.weight:.1f}\n"
    return s


def stringify_motor_states(states: List[MotorState], start: int, stop: int) -> str:
    s = ""
    for i, state in enumerate(states):
        if i < start or i >= stop:
            continue
        s += f"  Motor {i}: q={state.q:.2f}, dq={state.dq:.2f}, mode={state.mode:.2f}, temperature={state.temperature:.1f}\n"
    return s


def stringify_q_values(states: List[MotorState], indices: List[int]) -> str:
    q_values = []
    for i in indices:
        q_values.append(states[i].q)
    return "(" + ", ".join([f"{q:.4f}" for q in q_values]) + ")"


@dataclass
class BoosterLowLevelController:
    low_state_msg = None

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

    def close(self):
        logger.info("Closing BoosterLowLevelController")
        self.pub.CloseChannel()

    def _grab_low_state_handler(self, msg):
        self.low_state_msg = msg

    def read_latest_low_state(self, motor_indices: List[int]) -> str:
        # wait up to ~1s to get one packet
        for _ in range(500):
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


### PUNCHING MOTIONS
right_punch = [
    (-0.7589, -1.3272, 0.5087, -1.9598, -0.7834, 1.3089, 0.4808, 1.9911),
    (-0.8978, -1.2402, 0.5079, -1.8130, -0.4065, 1.0456, 0.4057, 2.1376),
    (-0.8974, -1.2360, 0.5152, -1.7409, -0.1352, 1.0086, 0.2024, 2.1376),
    (-0.4538, -1.1845, 0.5125, -2.1220, -1.0103, 0.8892, 0.7063, 1.6135),
    (-0.2539, -1.0636, 0.3721, -2.1223, -1.3846, 1.1311, 0.9173, 1.2270),
    (0.1108, -1.0628, 0.1204, -2.1227, -1.6222, 1.3302, 1.0794, 0.8356),
    (0.3367, -1.0846, 0.1219, -2.1231, -1.7725, 1.5091, 1.3296, 0.4931),
    (0.3553, -1.1017, 0.3088, -2.1231, -1.8187, 1.5946, 1.2869, 0.2558),
    (-0.0559, -1.1143, 0.3092, -2.1227, -1.6428, 1.3798, 1.1484, 0.7467),
    (-0.3538, -1.1269, 0.3092, -2.1223, -1.4193, 1.2783, 0.9539, 1.2335),
    (-0.6003, -1.2150, 0.3874, -2.0373, -1.0538, 1.1940, 0.6289, 1.7802),
    (-0.7673, -1.4000, 0.3889, -1.9282, -0.8055, 1.2246, 0.4423, 2.0689),
]

for i in range(len(right_punch)):
    right_punch[i] = tuple_to_joint_dict(
        LEFT_RIGHT_ARM_TORSO_JOINTS_INDICES, right_punch[i]
    )

left_punch = [
    (-0.7731, -1.5091, 0.4984, -1.7519, -0.7349, 1.3306, 0.4927, 1.9625),
    (-1.1465, -1.5122, 0.5854, -1.2175, -0.5201, 1.1223, 0.4931, 2.1151),
    (-1.4876, -1.5236, 0.8368, -0.7280, -0.3958, 0.8774, 0.4904, 2.1380),
    (-1.6276, -1.6495, 0.9943, -0.3000, -0.0956, 0.8213, 0.2161, 2.1380),
    (-1.7485, -1.7201, 1.0744, -0.1173, -0.1009, 0.8004, 0.2169, 2.1380),
    (-1.5543, -1.5961, 0.9413, -0.6167, -0.2981, 0.8553, 0.2199, 2.1380),
    (-0.9371, -1.3520, 0.5709, -1.4689, -0.6365, 1.0827, 0.4419, 2.0048),
    (-0.6106, -1.3127, 0.3962, -1.9499, -0.7574, 1.2993, 0.4950, 2.0636),
]

for i in range(len(left_punch)):
    left_punch[i] = tuple_to_joint_dict(
        LEFT_RIGHT_ARM_TORSO_JOINTS_INDICES, left_punch[i]
    )

EVENT_AXIS, EVENT_HAT, EVENT_BTN_DN, EVENT_BTN_UP, EVENT_REMOVE = (
    0x600,
    0x602,
    0x603,
    0x604,
    0x606,
)

if __name__ == "__main__":
    robot = BoosterLowLevelController()
    robot.init(network_interface="")

    robot.enable_arm_usage()

    def on_remote(rc: RemoteControllerState):
        ev = rc.event
        if ev == EVENT_BTN_DN:
            if rc.x:
                robot.send_command(right_punch, speed="slow", time_gap_s=0.05)
            if rc.y:
                robot.send_command(left_punch, speed="slow", time_gap_s=0.05)

    sub = B1RemoteControllerStateSubscriber(on_remote)
    sub.InitChannel()

    # --- clean, signal-friendly blocker ---
    stop = threading.Event()

    def _handle_stop(signum, frame):
        stop.set()

    # Handle Ctrl-C and kill
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    try:
        # Block here until a stop signal arrives
        stop.wait()  # no busy loop, no CPU burn
    finally:
        # Always clean up no matter how we exit
        try:
            sub.close()
        except Exception as e:
            logger.error("Close error:", e)
        logger.info("Stopping")
