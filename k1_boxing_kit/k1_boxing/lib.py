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
    def _change_mode(self, mode, label: str) -> int:
        """ChangeMode with the return code logged (0 = success)."""
        ret = self.loco_client.ChangeMode(mode)
        if ret == 0:
            logger.info("  %s: OK", label)
        else:
            logger.error("  %s: FAILED (error code %s)", label, ret)
        return ret

    def enable_upper_body_usage(self, already_standing: bool = False) -> None:
        """Get the robot standing/balancing, then enable custom arm control.

        Sequence mirrors the back-panel buttons: STAND (kPrepare) -> WALK (kWalking).
        If `already_standing` is True (you stood it via the buttons/app), we skip the
        mode changes and only turn on arm control.
        """
        from booster_robotics_sdk_python import RobotMode

        if not already_standing:
            logger.info("Standing up: prepare (ready) mode...")
            self._change_mode(RobotMode.kPrepare, "kPrepare")
            time.sleep(4)  # give it time to stand to the ready posture
            logger.info("Entering walking (balance) mode...")
            self._change_mode(RobotMode.kWalking, "kWalking")
            time.sleep(3)

        logger.info("Enabling upper-body custom control...")
        self.loco_client.UpperBodyCustomControl(True)
        time.sleep(1)
        self.log_current_mode()
        logger.info("Upper-body control ready. Legs remain balanced.")

    def get_mode(self):
        """Return the current RobotMode (or None if it can't be read)."""
        try:
            from booster_robotics_sdk_python import GetModeResponse

            resp = GetModeResponse()
            if self.loco_client.GetMode(resp) == 0:
                return getattr(resp, "mode", None)
        except Exception as exc:
            logger.warning("GetMode not available: %s", exc)
        return None

    def log_current_mode(self) -> None:
        """Query and log the robot's current mode (best-effort)."""
        mode = self.get_mode()
        if mode is None:
            logger.warning("Could not read current mode.")
        else:
            logger.info("Current robot mode: %s", mode)

    def is_walking(self) -> bool:
        """True if the robot is in WALK (balancing) mode."""
        try:
            from booster_robotics_sdk_python import RobotMode

            mode = self.get_mode()
            if mode is None:
                return False
            try:
                return int(mode) == int(RobotMode.kWalking)
            except Exception:
                return mode == RobotMode.kWalking
        except Exception:
            return False

    def damp(self) -> None:
        """Put the robot into damping mode (limp/compliant)."""
        try:
            from booster_robotics_sdk_python import RobotMode

            logger.info("Setting damping mode...")
            self.loco_client.ChangeMode(RobotMode.kDamping)
        except Exception as exc:
            logger.error("Failed to set damping mode: %s", exc)

    def set_ready(self) -> None:
        """Leave the robot standing in PREP (ready) mode - stiff, not limp."""
        try:
            from booster_robotics_sdk_python import RobotMode

            logger.info("Setting ready (prepare) mode - staying upright...")
            self._change_mode(RobotMode.kPrepare, "kPrepare")
        except Exception as exc:
            logger.error("Failed to set ready mode: %s", exc)

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

    def read_low_state_values(self, indices: List[int], timeout_s: float = 10.0):
        """Return the raw q (radians) at `indices` as a list of floats."""
        deadline = time.time() + timeout_s
        while self.low_state_msg is None and time.time() < deadline:
            time.sleep(0.01)
        if self.low_state_msg is None:
            raise RuntimeError("No LowState received; check network interface / wiring.")
        serial = self.low_state_msg.motor_state_serial
        return [serial[i].q for i in indices]

    def close(self) -> None:
        try:
            if self.pub:
                self.pub.CloseChannel()
            if self.sub:
                self.sub.CloseChannel()
        except Exception as exc:
            logger.error("Close error: %s", exc)
