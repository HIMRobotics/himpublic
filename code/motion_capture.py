#!/usr/bin/env python3
"""
Motion Capture - Record and playback robot motions

Records joint positions by pressing Enter at each pose.
The robot must be in a compliant mode where you can physically move the arms.

Usage:
    python motion_capture.py record football_throw
    python motion_capture.py playback football_throw
    python motion_capture.py list
"""

import json
import os
import sys
import time
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Output directory for motion files
MOTIONS_DIR = Path(__file__).parent.parent / "assets" / "motions"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("motion_capture")


@dataclass
class MotionKeyframe:
    """Single keyframe of joint positions."""
    timestamp: float
    joints: Dict[str, float]
    

@dataclass 
class MotionRecording:
    """Complete motion recording with metadata."""
    name: str
    created: str
    joint_names: List[str]
    keyframes: List[Dict]
    
    def save(self, filepath: Path) -> None:
        """Save recording to JSON file."""
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)
        logger.info(f"Saved recording to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path) -> "MotionRecording":
        """Load recording from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls(**data)


# Joint indices for recording (matching legacy code)
# These are the 8 arm + torso joints we care about
JOINT_INDICES = {
    "left_shoulder_pitch": 12,   # B1JointIndex.kLeftShoulderPitch
    "left_shoulder_roll": 13,    # B1JointIndex.kLeftShoulderRoll
    "left_elbow_pitch": 14,      # B1JointIndex.kLeftElbowPitch
    "left_elbow_yaw": 15,        # B1JointIndex.kLeftElbowYaw
    "right_shoulder_pitch": 16,  # B1JointIndex.kRightShoulderPitch
    "right_shoulder_roll": 17,   # B1JointIndex.kRightShoulderRoll
    "right_elbow_pitch": 18,     # B1JointIndex.kRightElbowPitch
    "right_elbow_yaw": 19,       # B1JointIndex.kRightElbowYaw
}


class MotionRecorder:
    """Records robot joint positions into motion files."""
    
    def __init__(self, network_interface: str = ""):
        self.network_interface = network_interface
        self.robot = None
        self.connected = False
        self.low_state_msg = None
        
    def connect(self) -> bool:
        """Connect to robot and set up subscribers."""
        try:
            from booster_robotics_sdk_python import (
                ChannelFactory,
                B1LowStateSubscriber,
                B1LocoClient,
                RobotMode,
            )
            
            logger.info("Initializing connection...")
            ChannelFactory.Instance().Init(
                domain_id=0, 
                network_interface=self.network_interface
            )
            
            # Subscribe to low-level state to read joint positions
            self.state_sub = B1LowStateSubscriber(handler=self._on_low_state)
            self.state_sub.InitChannel()
            
            # Loco client for mode changes
            self.loco_client = B1LocoClient()
            self.loco_client.Init()
            
            self.connected = True
            logger.info("Connected to robot!")
            return True
            
        except ImportError:
            logger.error("Booster SDK not installed!")
            logger.error("Install with: cd development/legacy/sdk && sudo ./install.sh")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def _on_low_state(self, msg) -> None:
        """Handler for low state messages."""
        self.low_state_msg = msg
    
    def set_recording_mode(self) -> bool:
        """Put robot into mode where arms can be manually positioned."""
        if not self.connected:
            logger.error("Not connected!")
            return False
        
        try:
            from booster_robotics_sdk_python import RobotMode
            
            logger.info("Setting robot to Custom mode...")
            self.loco_client.ChangeMode(RobotMode.kCustom)
            time.sleep(2)
            
            logger.info("Enabling hand end effector control...")
            self.loco_client.SwitchHandEndEffectorControlMode(True)
            time.sleep(1)
            
            logger.info("Robot ready for motion capture!")
            logger.info("You can now manually position the arms.")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set mode: {e}")
            return False
    
    def read_joint_positions(self) -> Optional[Dict[str, float]]:
        """Read current joint positions."""
        if self.low_state_msg is None:
            # Wait for state message
            for _ in range(100):  # 1 second timeout
                if self.low_state_msg is not None:
                    break
                time.sleep(0.01)
        
        if self.low_state_msg is None:
            logger.error("No state data received from robot!")
            return None
        
        motor_states = self.low_state_msg.motor_state_serial
        positions = {}
        
        for joint_name, idx in JOINT_INDICES.items():
            positions[joint_name] = motor_states[idx].q
        
        return positions
    
    def record_motion(self, name: str) -> Optional[MotionRecording]:
        """Interactive motion recording session."""
        if not self.connected:
            logger.error("Not connected to robot!")
            return None
        
        print("")
        print("=" * 50)
        print(f"RECORDING: {name}")
        print("=" * 50)
        print("")
        print("Instructions:")
        print("  1. Physically position Adam's arms")
        print("  2. Press ENTER to record the position")
        print("  3. Repeat for each keyframe")
        print("  4. Type 'done' when finished")
        print("  5. Type 'undo' to remove last keyframe")
        print("")
        
        keyframes = []
        start_time = time.time()
        
        while True:
            user_input = input(f"[{len(keyframes)} keyframes] Press ENTER to record, 'done' to finish: ").strip().lower()
            
            if user_input == "done":
                if len(keyframes) < 2:
                    print("Need at least 2 keyframes! Keep recording.")
                    continue
                break
            
            if user_input == "undo":
                if keyframes:
                    keyframes.pop()
                    print(f"Removed last keyframe. {len(keyframes)} remaining.")
                else:
                    print("No keyframes to undo.")
                continue
            
            # Record current position
            positions = self.read_joint_positions()
            if positions is None:
                print("Failed to read positions. Try again.")
                continue
            
            keyframe = {
                "timestamp": time.time() - start_time,
                "joints": positions,
            }
            keyframes.append(keyframe)
            
            # Print the recorded values
            print(f"  Recorded keyframe {len(keyframes)}:")
            for joint, val in positions.items():
                print(f"    {joint}: {val:.4f}")
        
        # Create recording
        recording = MotionRecording(
            name=name,
            created=datetime.now().isoformat(),
            joint_names=list(JOINT_INDICES.keys()),
            keyframes=keyframes,
        )
        
        # Save to file
        MOTIONS_DIR.mkdir(parents=True, exist_ok=True)
        filepath = MOTIONS_DIR / f"{name}.json"
        recording.save(filepath)
        
        print(f"\nRecording complete! {len(keyframes)} keyframes saved to {filepath}")
        return recording


class MotionPlayer:
    """Plays back recorded motions on the robot."""
    
    def __init__(self, network_interface: str = ""):
        self.network_interface = network_interface
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to robot for playback."""
        try:
            from booster_robotics_sdk_python import (
                ChannelFactory,
                B1LowCmdPublisher,
                B1LocoClient,
            )
            
            logger.info("Initializing connection for playback...")
            ChannelFactory.Instance().Init(
                domain_id=0,
                network_interface=self.network_interface
            )
            
            self.cmd_pub = B1LowCmdPublisher()
            self.cmd_pub.InitChannel()
            
            self.loco_client = B1LocoClient()
            self.loco_client.Init()
            
            self.connected = True
            logger.info("Connected for playback!")
            return True
            
        except ImportError:
            logger.error("Booster SDK not installed!")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def playback(self, recording: MotionRecording, speed: str = "slow", time_gap: float = 0.5) -> bool:
        """Play back a recorded motion."""
        if not self.connected:
            logger.error("Not connected!")
            return False
        
        try:
            from booster_robotics_sdk_python import (
                LowCmd, LowCmdType, MotorCmd, RobotMode,
            )
            
            # Speed settings (kp, kd, weight)
            speed_settings = {
                "slow": (20.0, 2.0, 1.0),
                "medium": (40.0, 2.0, 1.0),
                "fast": (80.0, 2.0, 1.0),
            }
            kp, kd, weight = speed_settings.get(speed, speed_settings["slow"])
            
            logger.info(f"Playing '{recording.name}' at {speed} speed...")
            logger.info(f"  {len(recording.keyframes)} keyframes, {time_gap}s gap")
            
            # Set mode
            self.loco_client.ChangeMode(RobotMode.kCustom)
            time.sleep(2)
            self.loco_client.SwitchHandEndEffectorControlMode(True)
            time.sleep(1)
            
            # Play each keyframe
            for i, keyframe in enumerate(recording.keyframes):
                logger.info(f"  Keyframe {i+1}/{len(recording.keyframes)}")
                
                # Create motor commands (23 joints total)
                motor_cmds = [MotorCmd() for _ in range(23)]
                
                # Set all to neutral first
                for mc in motor_cmds:
                    mc.mode = 0
                    mc.q = 0.0
                    mc.dq = 0.0
                    mc.tau = 0.0
                    mc.kp = 0.0
                    mc.kd = 0.0
                    mc.weight = 0.0
                
                # Set target positions for our joints
                for joint_name, q_val in keyframe["joints"].items():
                    idx = JOINT_INDICES[joint_name]
                    motor_cmds[idx].q = q_val
                    motor_cmds[idx].kp = kp
                    motor_cmds[idx].kd = kd
                    motor_cmds[idx].weight = weight
                
                # Send command
                cmd = LowCmd()
                cmd.cmd_type = LowCmdType.SERIAL
                cmd.motor_cmd = motor_cmds
                self.cmd_pub.Write(cmd)
                
                time.sleep(time_gap)
            
            logger.info("Playback complete!")
            return True
            
        except Exception as e:
            logger.error(f"Playback failed: {e}")
            return False


def list_recordings() -> List[str]:
    """List all saved motion recordings."""
    if not MOTIONS_DIR.exists():
        return []
    
    files = list(MOTIONS_DIR.glob("*.json"))
    return [f.stem for f in sorted(files)]


def load_recording(name: str) -> Optional[MotionRecording]:
    """Load a recording by name."""
    filepath = MOTIONS_DIR / f"{name}.json"
    if not filepath.exists():
        logger.error(f"Recording not found: {filepath}")
        return None
    return MotionRecording.load(filepath)


def demo_mode() -> None:
    """Run without robot connection (for testing)."""
    print("")
    print("=" * 50)
    print("DEMO MODE (No Robot Connected)")
    print("=" * 50)
    print("")
    print("This creates a sample motion file for testing.")
    print("")
    
    # Create sample keyframes (simulated football throw)
    sample_keyframes = [
        # Wind up - arm back
        {
            "timestamp": 0.0,
            "joints": {
                "left_shoulder_pitch": -0.5,
                "left_shoulder_roll": -1.4,
                "left_elbow_pitch": 0.7,
                "left_elbow_yaw": -1.7,
                "right_shoulder_pitch": -1.2,
                "right_shoulder_roll": 1.3,
                "right_elbow_pitch": 0.5,
                "right_elbow_yaw": 1.9,
            }
        },
        # Mid throw
        {
            "timestamp": 0.3,
            "joints": {
                "left_shoulder_pitch": -0.8,
                "left_shoulder_roll": -1.4,
                "left_elbow_pitch": 0.6,
                "left_elbow_yaw": -1.8,
                "right_shoulder_pitch": -0.4,
                "right_shoulder_roll": 1.1,
                "right_elbow_pitch": 0.3,
                "right_elbow_yaw": 2.0,
            }
        },
        # Release
        {
            "timestamp": 0.5,
            "joints": {
                "left_shoulder_pitch": -0.6,
                "left_shoulder_roll": -1.3,
                "left_elbow_pitch": 0.5,
                "left_elbow_yaw": -1.7,
                "right_shoulder_pitch": 0.3,
                "right_shoulder_roll": 0.9,
                "right_elbow_pitch": 0.2,
                "right_elbow_yaw": 2.1,
            }
        },
        # Follow through
        {
            "timestamp": 0.8,
            "joints": {
                "left_shoulder_pitch": -0.5,
                "left_shoulder_roll": -1.4,
                "left_elbow_pitch": 0.6,
                "left_elbow_yaw": -1.8,
                "right_shoulder_pitch": 0.6,
                "right_shoulder_roll": 0.7,
                "right_elbow_pitch": 0.4,
                "right_elbow_yaw": 1.8,
            }
        },
    ]
    
    recording = MotionRecording(
        name="sample_football_throw",
        created=datetime.now().isoformat(),
        joint_names=list(JOINT_INDICES.keys()),
        keyframes=sample_keyframes,
    )
    
    MOTIONS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = MOTIONS_DIR / "sample_football_throw.json"
    recording.save(filepath)
    
    print(f"Created sample recording: {filepath}")
    print(f"  {len(sample_keyframes)} keyframes")
    print("")
    print("When connected to the robot, run:")
    print("  python motion_capture.py playback sample_football_throw")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Record and playback robot motions")
    parser.add_argument("command", nargs="?", choices=["record", "playback", "list", "demo"],
                        help="Command to run")
    parser.add_argument("name", nargs="?", help="Motion name")
    parser.add_argument("--speed", type=str, default="slow", 
                        choices=["slow", "medium", "fast"],
                        help="Playback speed")
    parser.add_argument("--network", type=str, default="",
                        help="Network interface (e.g., 127.0.0.1)")
    
    args = parser.parse_args()
    
    if args.command == "list" or args.command is None:
        recordings = list_recordings()
        if recordings:
            print("Saved recordings:")
            for name in recordings:
                rec = load_recording(name)
                if rec:
                    print(f"  {name} ({len(rec.keyframes)} keyframes)")
        else:
            print("No recordings found.")
            print(f"  Motions directory: {MOTIONS_DIR}")
        return
    
    if args.command == "demo":
        demo_mode()
        return
    
    if args.command == "record":
        if not args.name:
            args.name = input("Enter motion name: ").strip()
        if not args.name:
            print("Motion name required!")
            sys.exit(1)
        
        recorder = MotionRecorder(network_interface=args.network)
        if not recorder.connect():
            print("\nTip: Run 'python motion_capture.py demo' to test without robot")
            sys.exit(1)
        
        if not recorder.set_recording_mode():
            sys.exit(1)
        
        recorder.record_motion(args.name)
    
    elif args.command == "playback":
        if not args.name:
            recordings = list_recordings()
            if not recordings:
                print("No recordings to play!")
                sys.exit(1)
            print("Available recordings:", ", ".join(recordings))
            args.name = input("Enter motion name: ").strip()
        
        recording = load_recording(args.name)
        if not recording:
            sys.exit(1)
        
        player = MotionPlayer(network_interface=args.network)
        if not player.connect():
            sys.exit(1)
        
        player.playback(recording, speed=args.speed)


if __name__ == "__main__":
    main()
