#!/usr/bin/env python3
"""
Quick Test - Single entry point for 30-minute robot session

This script provides a simple menu to:
1. Test voice playback
2. Test a built-in skill (wave)
3. Start motion capture
4. Playback recorded motions

Designed for efficient use during limited battery time.
"""

import os
import sys
import time
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("quick_test")

# Paths
CODE_DIR = Path(__file__).parent
AUDIO_DIR = CODE_DIR.parent / "assets" / "audio"
MOTIONS_DIR = CODE_DIR.parent / "assets" / "motions"


class RobotConnection:
    """Manages robot connection state."""
    
    def __init__(self):
        self.connected = False
        self.loco_client = None
        self.cmd_pub = None
        self.state_sub = None
        self.low_state_msg = None
        
    def connect(self, network_interface: str = "") -> bool:
        """Connect to the robot."""
        if self.connected:
            logger.info("Already connected!")
            return True
            
        try:
            from booster_robotics_sdk_python import (
                ChannelFactory,
                B1LowCmdPublisher,
                B1LowStateSubscriber,
                B1LocoClient,
            )
            
            logger.info("Connecting to robot...")
            ChannelFactory.Instance().Init(
                domain_id=0,
                network_interface=network_interface
            )
            
            self.cmd_pub = B1LowCmdPublisher()
            self.cmd_pub.InitChannel()
            
            self.state_sub = B1LowStateSubscriber(handler=self._on_low_state)
            self.state_sub.InitChannel()
            
            self.loco_client = B1LocoClient()
            self.loco_client.Init()
            
            self.connected = True
            logger.info("Connected!")
            return True
            
        except ImportError:
            logger.error("ERROR: Booster SDK not installed!")
            logger.error("Run: cd development/legacy/sdk && sudo ./install.sh")
            logger.error("Then: pip install pybind11 && cd build && cmake .. -DBUILD_PYTHON_BINDING=on && make && sudo make install")
            return False
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def _on_low_state(self, msg):
        self.low_state_msg = msg


# Global robot connection
robot = RobotConnection()


def play_audio_file(filepath: str) -> bool:
    """Play an audio file."""
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return False
    
    logger.info(f"Playing: {Path(filepath).name}")
    
    # Try different audio players
    players = [
        ["aplay", filepath],           # Linux ALSA (robot)
        ["paplay", filepath],          # PulseAudio
        ["afplay", filepath],          # macOS
        ["mpv", "--no-video", filepath],  # Cross-platform
    ]
    
    for player_cmd in players:
        try:
            result = subprocess.run(player_cmd, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    logger.error("No audio player found!")
    return False


def test_voice() -> None:
    """Test voice playback."""
    print("")
    print("=" * 40)
    print("TEST VOICE PLAYBACK")
    print("=" * 40)
    
    # Check for audio files
    if not AUDIO_DIR.exists():
        print(f"No audio directory found at {AUDIO_DIR}")
        print("Generate audio first:")
        print("  python voice_tts.py --generate")
        return
    
    audio_files = list(AUDIO_DIR.glob("*.mp3")) + list(AUDIO_DIR.glob("*.wav"))
    if not audio_files:
        print("No audio files found!")
        print("Generate audio first:")
        print("  python voice_tts.py --generate")
        return
    
    print(f"\nFound {len(audio_files)} audio files:")
    for i, f in enumerate(sorted(audio_files)[:10], 1):
        print(f"  {i}. {f.name}")
    if len(audio_files) > 10:
        print(f"  ... and {len(audio_files) - 10} more")
    
    print("")
    choice = input("Enter number to play (or 'all' for first 3): ").strip()
    
    if choice.lower() == "all":
        for f in sorted(audio_files)[:3]:
            play_audio_file(str(f))
            time.sleep(0.5)
    elif choice.isdigit():
        idx = int(choice) - 1
        files = sorted(audio_files)
        if 0 <= idx < len(files):
            play_audio_file(str(files[idx]))
        else:
            print("Invalid selection")


def test_skill() -> None:
    """Test a built-in robot skill."""
    print("")
    print("=" * 40)
    print("TEST BUILT-IN SKILL")
    print("=" * 40)
    
    if not robot.connect():
        return
    
    try:
        from booster_robotics_sdk_python import RobotMode
        
        print("\nAvailable test actions:")
        print("  1. Wave (safe, standing)")
        print("  2. Head nod")
        print("  3. Stand pose")
        print("  4. Custom mode (for motion capture)")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            logger.info("Testing wave motion...")
            # Simplified wave using arm joints
            test_arm_motion("wave")
            
        elif choice == "2":
            logger.info("Testing head nod...")
            test_head_motion()
            
        elif choice == "3":
            logger.info("Standing pose...")
            robot.loco_client.ChangeMode(RobotMode.kPrepare)
            time.sleep(2)
            logger.info("Robot in standing pose")
            
        elif choice == "4":
            logger.info("Entering custom mode...")
            robot.loco_client.ChangeMode(RobotMode.kCustom)
            time.sleep(2)
            robot.loco_client.SwitchHandEndEffectorControlMode(True)
            time.sleep(1)
            logger.info("Robot in custom mode - arms can be manually positioned!")
        
        else:
            print("Invalid choice")
            
    except Exception as e:
        logger.error(f"Skill test failed: {e}")


def test_arm_motion(motion_type: str) -> None:
    """Test simple arm motion."""
    try:
        from booster_robotics_sdk_python import (
            LowCmd, LowCmdType, MotorCmd, RobotMode,
        )
        
        # Enter custom mode first
        robot.loco_client.ChangeMode(RobotMode.kCustom)
        time.sleep(2)
        robot.loco_client.SwitchHandEndEffectorControlMode(True)
        time.sleep(1)
        
        # Simple wave motion - move right arm
        joint_indices = {
            "right_shoulder_pitch": 16,
            "right_shoulder_roll": 17,
            "right_elbow_pitch": 18,
        }
        
        # Wave keyframes
        if motion_type == "wave":
            keyframes = [
                {"right_shoulder_pitch": -1.5, "right_shoulder_roll": 0.3, "right_elbow_pitch": 0.5},
                {"right_shoulder_pitch": -1.5, "right_shoulder_roll": 0.5, "right_elbow_pitch": 0.3},
                {"right_shoulder_pitch": -1.5, "right_shoulder_roll": 0.3, "right_elbow_pitch": 0.5},
                {"right_shoulder_pitch": -1.5, "right_shoulder_roll": 0.5, "right_elbow_pitch": 0.3},
                {"right_shoulder_pitch": -0.7, "right_shoulder_roll": 1.3, "right_elbow_pitch": 0.5},
            ]
        else:
            keyframes = []
        
        kp, kd, weight = 20.0, 2.0, 1.0  # Slow/safe
        
        for kf in keyframes:
            motor_cmds = [MotorCmd() for _ in range(23)]
            for mc in motor_cmds:
                mc.mode = 0
                mc.q = 0.0
                mc.dq = 0.0
                mc.tau = 0.0
                mc.kp = 0.0
                mc.kd = 0.0
                mc.weight = 0.0
            
            for joint_name, q_val in kf.items():
                idx = joint_indices[joint_name]
                motor_cmds[idx].q = q_val
                motor_cmds[idx].kp = kp
                motor_cmds[idx].kd = kd
                motor_cmds[idx].weight = weight
            
            cmd = LowCmd()
            cmd.cmd_type = LowCmdType.SERIAL
            cmd.motor_cmd = motor_cmds
            robot.cmd_pub.Write(cmd)
            time.sleep(0.4)
        
        logger.info("Wave complete!")
        
    except Exception as e:
        logger.error(f"Arm motion failed: {e}")


def test_head_motion() -> None:
    """Test head nod motion."""
    try:
        from booster_robotics_sdk_python import (
            LowCmd, LowCmdType, MotorCmd, B1JointIndex,
        )
        
        head_pitch_idx = B1JointIndex.kHeadPitch.value
        
        # Head nod positions
        positions = [0.0, 0.3, 0.0, 0.3, 0.0]
        
        for pos in positions:
            motor_cmds = [MotorCmd() for _ in range(23)]
            for mc in motor_cmds:
                mc.mode = 0
                mc.q = 0.0
                mc.dq = 0.0
                mc.tau = 0.0
                mc.kp = 0.0
                mc.kd = 0.0
                mc.weight = 0.0
            
            motor_cmds[head_pitch_idx].q = pos
            motor_cmds[head_pitch_idx].kp = 4.0
            motor_cmds[head_pitch_idx].kd = 1.0
            motor_cmds[head_pitch_idx].weight = 1.0
            
            cmd = LowCmd()
            cmd.cmd_type = LowCmdType.PARALLEL
            cmd.motor_cmd = motor_cmds
            robot.cmd_pub.Write(cmd)
            time.sleep(0.3)
        
        logger.info("Head nod complete!")
        
    except Exception as e:
        logger.error(f"Head motion failed: {e}")


def motion_capture_menu() -> None:
    """Motion capture submenu."""
    print("")
    print("=" * 40)
    print("MOTION CAPTURE")
    print("=" * 40)
    
    print("\nOptions:")
    print("  1. Record new motion")
    print("  2. Play back motion")
    print("  3. List recordings")
    print("  4. Create demo recording (no robot)")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == "1":
        name = input("Motion name (e.g., football_throw): ").strip()
        if name:
            os.system(f"python {CODE_DIR}/motion_capture.py record {name}")
    
    elif choice == "2":
        # List available
        if MOTIONS_DIR.exists():
            files = list(MOTIONS_DIR.glob("*.json"))
            if files:
                print("\nAvailable recordings:")
                for f in files:
                    print(f"  - {f.stem}")
        name = input("Motion name to play: ").strip()
        if name:
            speed = input("Speed (slow/medium/fast) [slow]: ").strip() or "slow"
            os.system(f"python {CODE_DIR}/motion_capture.py playback {name} --speed {speed}")
    
    elif choice == "3":
        os.system(f"python {CODE_DIR}/motion_capture.py list")
    
    elif choice == "4":
        os.system(f"python {CODE_DIR}/motion_capture.py demo")


def show_status() -> None:
    """Show current status."""
    print("")
    print("=" * 40)
    print("SYSTEM STATUS")
    print("=" * 40)
    
    # Check SDK
    try:
        import booster_robotics_sdk_python
        print("  SDK: Installed")
    except ImportError:
        print("  SDK: NOT INSTALLED")
    
    # Check audio files
    audio_count = 0
    if AUDIO_DIR.exists():
        audio_count = len(list(AUDIO_DIR.glob("*.mp3"))) + len(list(AUDIO_DIR.glob("*.wav")))
    print(f"  Audio files: {audio_count}")
    
    # Check motion recordings
    motion_count = 0
    if MOTIONS_DIR.exists():
        motion_count = len(list(MOTIONS_DIR.glob("*.json")))
    print(f"  Motion recordings: {motion_count}")
    
    # Check ElevenLabs key
    if os.environ.get("ELEVENLABS_API_KEY"):
        print("  ElevenLabs API: Configured")
    else:
        print("  ElevenLabs API: NOT SET")
    
    # Robot connection
    print(f"  Robot connected: {robot.connected}")


def main_menu() -> None:
    """Main interactive menu."""
    print("")
    print("=" * 50)
    print("   ADAM QUICK TEST")
    print("   30-Minute Session Helper")
    print("=" * 50)
    
    while True:
        print("")
        print("Options:")
        print("  1. Test voice playback")
        print("  2. Test built-in skill")
        print("  3. Motion capture")
        print("  4. Generate voice files (ElevenLabs)")
        print("  5. Show status")
        print("  Q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == "1":
            test_voice()
        
        elif choice == "2":
            test_skill()
        
        elif choice == "3":
            motion_capture_menu()
        
        elif choice == "4":
            os.system(f"python {CODE_DIR}/voice_tts.py --generate")
        
        elif choice == "5":
            show_status()
        
        elif choice == "q":
            print("\nGoodbye! Don't forget to charge Adam!")
            break
        
        else:
            print("Invalid choice. Try again.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick test runner for Adam")
    parser.add_argument("--voice", action="store_true", help="Jump to voice test")
    parser.add_argument("--skill", action="store_true", help="Jump to skill test")
    parser.add_argument("--motion", action="store_true", help="Jump to motion capture")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.voice:
        test_voice()
    elif args.skill:
        test_skill()
    elif args.motion:
        motion_capture_menu()
    else:
        main_menu()


if __name__ == "__main__":
    main()
