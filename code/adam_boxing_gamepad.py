#!/usr/bin/env python3
"""
Adam Boxing - Gamepad Controlled Punching

Throw punches with a game controller. Each button fires a punch pose, then Adam
snaps back to a boxing guard automatically.

SAFETY - READ BEFORE ENABLING THE ROBOT
----------------------------------------
This script commands ONLY the 8 arm joints, with low gains, small ranges, and an
automatic return to the guard pose. It intentionally does NOT command the legs, so
the robot's onboard controller keeps authority over balance.

Even so, low-level joint commands are risky. Before setting ENABLE_ROBOT = True:
  1. Start the robot in DAMP mode.
  2. Have a spotter present, and support/hang the robot the first few runs.
  3. Verify each punch pose at very low speed and small range, then tune.
  4. Keep the tuned KP low. Higher gains = harder/faster arm motion = more risk.

By default ENABLE_ROBOT = False, so this runs in SIMULATION mode and only prints
what it would do. Nothing moves until you deliberately flip the flag.

Usage:
    python adam_boxing_gamepad.py                 # simulation (no robot)
    # set ENABLE_ROBOT = True below, then:
    python adam_boxing_gamepad.py --network 127.0.0.1
"""

import sys
import time
import argparse
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

try:
    import pygame
except ImportError:
    print("pygame not installed. Run: pip install pygame")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("adam_boxing")

# ============================================
# CONFIGURATION
# ============================================
ROBOT_IP = "192.168.1.100"  # Informational; connection uses --network interface

# SAFETY GATE: keep False until you've validated poses on a supported robot.
ENABLE_ROBOT = False

# Low-level control gains for the arm joints. Keep these LOW.
# (kp, kd, weight) - higher kp/weight = stiffer/faster/harder punches.
KP = 15.0
KD = 2.0
WEIGHT = 1.0

# Timing (seconds)
PUNCH_DURATION = 0.18   # time held at the extended punch pose
RETURN_DURATION = 0.22  # time given to settle back into guard
MIN_TIME_BETWEEN_PUNCHES = 0.15  # simple debounce so mashing doesn't queue up

# Total joints in the low-level serial command (matches motion_capture.py).
NUM_JOINTS = 23

# Arm joint indices on the K1 (matches motion_capture.py JOINT_INDICES).
ARM_JOINTS = {
    "left_shoulder_pitch": 12,
    "left_shoulder_roll": 13,
    "left_elbow_pitch": 14,
    "left_elbow_yaw": 15,
    "right_shoulder_pitch": 16,
    "right_shoulder_roll": 17,
    "right_elbow_pitch": 18,
    "right_elbow_yaw": 19,
}

# Conservative safety clamp (radians) applied to every commanded arm joint.
# Tighten these once you know your robot's comfortable working range.
JOINT_LIMIT = 2.0

# ============================================
# BOXING POSES (radians)
# ============================================
# NOTE: These are STARTING ESTIMATES. Tune them on a supported robot, or better,
# capture real poses with motion_capture.py and paste the values here.
# Missing joints in a punch fall back to the GUARD value.

GUARD = {
    "left_shoulder_pitch": -0.6,
    "left_shoulder_roll": -0.6,
    "left_elbow_pitch": 1.3,
    "left_elbow_yaw": 0.0,
    "right_shoulder_pitch": -0.6,
    "right_shoulder_roll": 0.6,
    "right_elbow_pitch": 1.3,
    "right_elbow_yaw": 0.0,
}

# Each move only overrides the joints it changes; the rest stay at GUARD.
MOVES: Dict[str, Dict[str, float]] = {
    "jab": {  # left arm straight out
        "left_shoulder_pitch": -1.0,
        "left_shoulder_roll": -0.2,
        "left_elbow_pitch": 0.1,
    },
    "cross": {  # right arm straight out
        "right_shoulder_pitch": -1.0,
        "right_shoulder_roll": 0.2,
        "right_elbow_pitch": 0.1,
    },
    "left_hook": {  # left arm swings across, elbow bent
        "left_shoulder_pitch": -1.1,
        "left_shoulder_roll": -1.0,
        "left_elbow_pitch": 0.9,
    },
    "right_hook": {  # right arm swings across, elbow bent
        "right_shoulder_pitch": -1.1,
        "right_shoulder_roll": 1.0,
        "right_elbow_pitch": 0.9,
    },
    "left_uppercut": {  # left arm drives up from below
        "left_shoulder_pitch": -0.2,
        "left_shoulder_roll": -0.3,
        "left_elbow_pitch": 1.6,
    },
    "right_uppercut": {  # right arm drives up from below
        "right_shoulder_pitch": -0.2,
        "right_shoulder_roll": 0.3,
        "right_elbow_pitch": 1.6,
    },
}

# ============================================
# GAMEPAD BUTTON MAP
# ============================================
# Xbox-style defaults. Run test_gamepad.py to confirm your controller's numbers.
BUTTON_MAP = {
    2: "jab",             # X
    1: "cross",           # B
    3: "left_hook",       # Y
    0: "right_hook",      # A
    4: "left_uppercut",   # LB
    5: "right_uppercut",  # RB
}
GUARD_BUTTONS = {6}      # Back/Select -> force return to guard
QUIT_BUTTONS = {7, 9}    # Start/Menu -> quit


def resolve_pose(move_name: str) -> Dict[str, float]:
    """Build a full arm pose for a move, filling gaps from GUARD and clamping."""
    pose = dict(GUARD)
    pose.update(MOVES.get(move_name, {}))
    return {
        joint: max(-JOINT_LIMIT, min(JOINT_LIMIT, value))
        for joint, value in pose.items()
    }


@dataclass
class BoxingController:
    network_interface: str = ""
    connected: bool = False
    joystick: Optional["pygame.joystick.Joystick"] = None
    cmd_pub: object = field(default=None, repr=False)
    loco_client: object = field(default=None, repr=False)
    _last_punch_time: float = 0.0

    # ---- Robot connection -------------------------------------------------
    def connect_robot(self) -> bool:
        """Connect for low-level arm control. No-op in simulation mode."""
        if not ENABLE_ROBOT:
            logger.info("SIMULATION mode (ENABLE_ROBOT = False) - robot will not move.")
            self.connected = False
            return False

        try:
            from booster_robotics_sdk_python import (
                ChannelFactory,
                B1LowCmdPublisher,
                B1LocoClient,
                RobotMode,
            )

            logger.info("Connecting to robot (%s)...", self.network_interface or "default")
            ChannelFactory.Instance().Init(
                domain_id=0, network_interface=self.network_interface
            )

            self.cmd_pub = B1LowCmdPublisher()
            self.cmd_pub.InitChannel()

            self.loco_client = B1LocoClient()
            self.loco_client.Init()

            # Enter custom mode so we can send arm joint targets.
            # Legs are left un-commanded (weight 0) so they hold their controller.
            self.loco_client.ChangeMode(RobotMode.kCustom)
            time.sleep(2)

            self.connected = True
            logger.info("Robot connected. Starting from guard pose.")
            self._send_pose(resolve_pose("guard") if "guard" in MOVES else GUARD)
            return True

        except ImportError:
            logger.error("Booster SDK not installed - falling back to simulation.")
            self.connected = False
            return False
        except Exception as exc:
            logger.error("Robot connection failed (%s) - falling back to simulation.", exc)
            self.connected = False
            return False

    # ---- Gamepad connection ----------------------------------------------
    def connect_gamepad(self) -> bool:
        """Initialize pygame and grab the first controller."""
        try:
            pygame.init()
            pygame.joystick.init()

            if pygame.joystick.get_count() == 0:
                logger.error("No gamepad detected! Connect a controller and retry.")
                return False

            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            logger.info("Connected to gamepad: %s", self.joystick.get_name())
            return True
        except Exception as exc:
            logger.error("Gamepad init failed: %s", exc)
            return False

    # ---- Motion ----------------------------------------------------------
    def _send_pose(self, pose: Dict[str, float]) -> None:
        """Send target angles for the arm joints only. Legs stay un-commanded."""
        if not (self.connected and self.cmd_pub):
            return
        try:
            from booster_robotics_sdk_python import LowCmd, LowCmdType, MotorCmd

            motor_cmds = [MotorCmd() for _ in range(NUM_JOINTS)]
            for mc in motor_cmds:
                # weight 0 => this joint is not driven by us (keeps legs free).
                mc.mode = 0
                mc.q = 0.0
                mc.dq = 0.0
                mc.tau = 0.0
                mc.kp = 0.0
                mc.kd = 0.0
                mc.weight = 0.0

            for joint_name, angle in pose.items():
                idx = ARM_JOINTS[joint_name]
                motor_cmds[idx].q = angle
                motor_cmds[idx].kp = KP
                motor_cmds[idx].kd = KD
                motor_cmds[idx].weight = WEIGHT

            cmd = LowCmd()
            cmd.cmd_type = LowCmdType.SERIAL
            cmd.motor_cmd = motor_cmds
            self.cmd_pub.Write(cmd)
        except Exception as exc:
            logger.error("Failed to send pose: %s", exc)

    def throw_punch(self, move_name: str) -> None:
        """Fire a punch pose, then automatically return to guard."""
        now = time.time()
        if now - self._last_punch_time < MIN_TIME_BETWEEN_PUNCHES:
            return
        self._last_punch_time = now

        logger.info(">>> %s", move_name.upper().replace("_", " "))
        self._send_pose(resolve_pose(move_name))
        time.sleep(PUNCH_DURATION)

        logger.info("    ...back to guard")
        self._send_pose(GUARD)
        time.sleep(RETURN_DURATION)

    def go_to_guard(self) -> None:
        logger.info(">>> GUARD")
        self._send_pose(GUARD)

    # ---- Main loop -------------------------------------------------------
    def run(self) -> None:
        if not self.connect_gamepad():
            return

        print("\n" + "=" * 50)
        print("ADAM BOXING (Gamepad) - Ready!")
        print("=" * 50)
        print("\nButton mappings:")
        for button, move in BUTTON_MAP.items():
            print(f"  Button {button} = {move.replace('_', ' ')}")
        print(f"  Button(s) {sorted(GUARD_BUTTONS)} = return to guard")
        print(f"  Button(s) {sorted(QUIT_BUTTONS)} = quit")
        if not self.connected:
            print("\n[SIMULATION] Printing punches only - robot is not moving.")
        print("-" * 50)

        running = True
        try:
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.JOYBUTTONDOWN:
                        button = event.button
                        if button in QUIT_BUTTONS:
                            running = False
                            break
                        if button in GUARD_BUTTONS:
                            self.go_to_guard()
                        elif button in BUTTON_MAP:
                            self.throw_punch(BUTTON_MAP[button])
                        else:
                            logger.info("Unmapped button: %s", button)
                time.sleep(0.01)  # avoid CPU spin
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Return to guard and clean up."""
        try:
            if self.connected:
                self.go_to_guard()
        finally:
            pygame.quit()
            logger.info("\nDone. Stay safe out there.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Gamepad-controlled boxing for Adam")
    parser.add_argument(
        "--network", type=str, default="",
        help="Network interface for the robot (e.g., 127.0.0.1). Ignored in simulation.",
    )
    args = parser.parse_args()

    controller = BoxingController(network_interface=args.network)
    controller.connect_robot()  # falls back to simulation on any failure
    controller.run()


if __name__ == "__main__":
    main()
