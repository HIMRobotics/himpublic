"""Low-level K1 controller for balance-safe upper-body (arm) motion.

Ported from KyleAlanJeffrey/booster and adapted for the K1:
  - Fight mode enables UpperBodyCustomControl so the legs stay on the onboard
    balance controller (kWalking) while we drive only the arms.
  - Defaults to the SOFT (slow) gain profile.
  - Clamps every commanded arm angle as a last-resort safety guard.
"""

from dataclasses import dataclass, field
import logging
import time
from typing import Dict, List, Optional

from .helpers import SpeedType, clamp, stringify_q_values

logger = logging.getLogger("k1_boxing")

# The SDK serial motor array length (B1 family). himpublic/code/motion_capture.py
# uses this same length for the K1.
NUM_MOTORS = 23

# PD gains. Keep these conservative - higher kp = harder/faster arm motion.
KP_HARD = 80.0
KP_MED = 40.0
KP_SOFT = 20.0
KD_MED = 2.0
WEIGHT_MED = 1.0

# Last-resort clamp (radians) on every commanded arm angle. The recorded poses
# stay within this; it only catches corrupted values.
JOINT_LIMIT = 3.0


def _get_pd_gains(speed: SpeedType):
    if speed == "fast":
        return KP_HARD, KD_MED, WEIGHT_MED
    if speed == "medium":
        return KP_MED, KD_MED, WEIGHT_MED
    return KP_SOFT, KD_MED, WEIGHT_MED


@dataclass
class BoosterLowLevelController:
    network_interface: str = ""
    low_state_msg: object = field(default=None, repr=False)
    _motor_cmds: list = field(default=None, repr=False)
    pub: object = field(default=None, repr=False)
    sub: object = field(default=None, repr=False)
    loco_client: object = field(default=None, repr=False)

    def init(self, network_domain: int = 0, network_interface: str = "") -> None:
        from booster_robotics_sdk_python import (
            ChannelFactory,
            B1LowCmdPublisher,
            B1LowStateSubscriber,
            B1LocoClient,
            MotorCmd,
        )

        logger.info("Initializing K1 controller (%s)...", network_interface or "default")
        ChannelFactory.Instance().Init(
            domain_id=network_domain, network_interface=network_interface
        )

        self.pub = B1LowCmdPublisher()
        self.pub.InitChannel()

        self.sub = B1LowStateSubscriber(handler=self._grab_low_state)
        self.sub.InitChannel()

        self.loco_client = B1LocoClient()
        self.loco_client.Init()

        self._motor_cmds = self._neutral_cmds(MotorCmd)
        logger.info("K1 controller initialized.")

    @staticmethod
    def _neutral_cmds(motor_cmd_cls) -> list:
        cmds = []
        for _ in range(NUM_MOTORS):
            mc = motor_cmd_cls()
            mc.mode = 0
            mc.q = 0.0
            mc.dq = 0.0
            mc.tau = 0.0
            mc.kp = 0.0
            mc.kd = 0.0
            mc.weight = 0.0
            cmds.append(mc)
        return cmds

    def _grab_low_state(self, msg) -> None:
        self.low_state_msg = msg

    # ---- Modes -----------------------------------------------------------
    def enable_upper_body_usage(self) -> None:
        """Keep legs balancing (kWalking) while enabling custom arm control."""
        from booster_robotics_sdk_python import RobotMode

        logger.info("Preparing robot...")
        self.loco_client.ChangeMode(RobotMode.kPrepare)
        time.sleep(2)
        logger.info("Entering walking (balance) mode...")
        self.loco_client.ChangeMode(RobotMode.kWalking)
        time.sleep(2)
        logger.info("Enabling upper-body custom control...")
        self.loco_client.UpperBodyCustomControl(True)
        time.sleep(1)
        logger.info("Upper-body control ready. Legs remain balanced.")

    def damp(self) -> None:
        """Put the robot into damping mode (safe, compliant)."""
        try:
            from booster_robotics_sdk_python import RobotMode

            logger.info("Setting damping mode...")
            self.loco_client.ChangeMode(RobotMode.kDamping)
        except Exception as exc:
            logger.error("Failed to set damping mode: %s", exc)

    # ---- Commands --------------------------------------------------------
    def _send(self) -> None:
        from booster_robotics_sdk_python import LowCmd, LowCmdType

        msg = LowCmd()
        msg.cmd_type = LowCmdType.SERIAL
        msg.motor_cmd = self._motor_cmds
        if not self.pub.Write(msg):
            raise RuntimeError("Publish LowCmd failed")

    def send_command(
        self,
        frames: List[Dict[int, float]],
        speed: SpeedType = "slow",
        time_gap_s: float = 0.05,
    ) -> None:
        """Play a sequence of arm poses (index -> absolute angle) frame by frame."""
        kp, kd, weight = _get_pd_gains(speed)
        for frame in frames:
            for idx, angle in frame.items():
                if 0 <= idx < len(self._motor_cmds):
                    self._motor_cmds[idx].q = clamp(angle, JOINT_LIMIT)
                    self._motor_cmds[idx].kp = kp
                    self._motor_cmds[idx].kd = kd
                    self._motor_cmds[idx].weight = weight
                else:
                    logger.warning("Skipping out-of-range joint index %s", idx)
            self._send()
            time.sleep(time_gap_s)

    # ---- Diagnostics -----------------------------------------------------
    def read_low_state_q(self, indices: List[int], timeout_s: float = 10.0) -> str:
        """Block briefly for a state packet, then format q values at `indices`."""
        deadline = time.time() + timeout_s
        while self.low_state_msg is None and time.time() < deadline:
            time.sleep(0.01)
        if self.low_state_msg is None:
            raise RuntimeError("No LowState received; check network interface / wiring.")
        return stringify_q_values(self.low_state_msg.motor_state_serial, indices)

    def close(self) -> None:
        try:
            if self.pub:
                self.pub.CloseChannel()
            if self.sub:
                self.sub.CloseChannel()
        except Exception as exc:
            logger.error("Close error: %s", exc)
