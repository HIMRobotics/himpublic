#!/usr/bin/env python3
"""
Test Booster SDK Connection
Run this first to verify you can talk to the robot.
"""

import sys

# TODO: Update this import once SDK is installed
# from booster_robotics_sdk import Robot

# ============================================
# CONFIGURATION - UPDATE THESE
# ============================================
ROBOT_IP = "192.168.1.100"  # Replace with your robot's IP
# ============================================


def test_connection():
    """Test basic connection to the robot."""
    print(f"Connecting to robot at {ROBOT_IP}...")

    try:
        # Uncomment once SDK is installed:
        # robot = Robot(ROBOT_IP)
        # robot.connect()
        # print("Connected!")
        # print(f"Robot status: {robot.get_status()}")

        # Placeholder until SDK installed
        print("SDK not installed yet. Install it first:")
        print("  cd booster_robotics_sdk")
        print("  sudo ./install.sh")
        print("  cd python && pip install -e .")
        return False

    except Exception as e:
        print(f"Connection failed: {e}")
        return False

    return True


def test_basic_commands():
    """Test basic robot commands."""
    print("\nTesting basic commands...")

    # Uncomment once SDK is installed:
    # robot = Robot(ROBOT_IP)
    # robot.connect()

    # Test stand
    # print("Standing up...")
    # robot.stand()

    # Test head movement
    # print("Moving head...")
    # robot.set_head_position(yaw=0.3, pitch=0.0)
    # time.sleep(1)
    # robot.set_head_position(yaw=-0.3, pitch=0.0)
    # time.sleep(1)
    # robot.set_head_position(yaw=0.0, pitch=0.0)

    print("Basic commands test placeholder - install SDK first")


def list_actions():
    """List all available built-in actions."""
    print("\nListing available actions...")

    # Uncomment once SDK is installed:
    # robot = Robot(ROBOT_IP)
    # robot.connect()
    # actions = robot.list_actions()
    # print("Available actions:")
    # for action in actions:
    #     print(f"  - {action}")

    print("Action list placeholder - install SDK first")


def main():
    print("=" * 50)
    print("BOOSTER SDK CONNECTION TEST")
    print("=" * 50)

    if not test_connection():
        print("\nConnection failed. Check:")
        print("  1. Robot is powered on")
        print("  2. Robot IP is correct")
        print("  3. You're on the same network")
        print("  4. SDK is installed")
        sys.exit(1)

    test_basic_commands()
    list_actions()

    print("\n" + "=" * 50)
    print("All tests complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
