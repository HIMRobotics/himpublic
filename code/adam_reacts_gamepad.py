#!/usr/bin/env python3
"""
Adam Reacts - Gamepad Version

Control Adam with a gamepad/controller instead of keyboard.
"""

import sys
import os
import time

try:
    import pygame
except ImportError:
    print("pygame not installed. Run: pip install pygame")
    sys.exit(1)

# TODO: Uncomment once SDK is installed
# from booster_robotics_sdk import Robot

# ============================================
# CONFIGURATION - UPDATE THESE
# ============================================
ROBOT_IP = "192.168.1.100"  # Replace with your robot's IP
AUDIO_DIR = "../assets/audio"

# Map gamepad buttons to reactions
# Update these numbers based on test_gamepad.py output
BUTTON_MAP = {
    0: "celebrate",      # A button (Xbox) / X button (PS)
    1: "disappointed",   # B button (Xbox) / Circle (PS)
    2: "wave",          # X button (Xbox) / Square (PS)
    3: "dance",         # Y button (Xbox) / Triangle (PS)
    4: "high_five",     # LB (Xbox) / L1 (PS)
}
# ============================================


REACTIONS = {
    "celebrate": {
        "motion": "celebrate",
        "phrase": "GOOOAL!",
    },
    "disappointed": {
        "motion": "sad_pose",
        "phrase": "Aww, so close!",
    },
    "wave": {
        "motion": "wave",
        "phrase": "Hey there!",
    },
    "dance": {
        "motion": "dance",
        "phrase": None,
    },
    "high_five": {
        "motion": "high_five",
        "phrase": "Up top!",
    },
}


class AdamReactsGamepad:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.robot = None
        self.connected = False
        self.joystick = None

    def connect_robot(self):
        """Connect to the robot."""
        print(f"Connecting to robot at {self.robot_ip}...")
        try:
            # TODO: Uncomment once SDK installed
            # self.robot = Robot(self.robot_ip)
            # self.robot.connect()
            # self.connected = True
            print("Robot connection placeholder - SDK not installed yet")
            self.connected = False
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False
        return self.connected

    def connect_gamepad(self):
        """Connect to the gamepad."""
        pygame.init()
        pygame.joystick.init()

        if pygame.joystick.get_count() == 0:
            print("No gamepad detected!")
            return False

        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()
        print(f"Connected to: {self.joystick.get_name()}")
        return True

    def play_motion(self, motion_name):
        """Play a motion on the robot."""
        print(f"  Playing motion: {motion_name}")
        if self.connected and self.robot:
            # TODO: Uncomment once SDK installed
            # self.robot.play_action(motion_name)
            pass

    def speak(self, phrase):
        """Make the robot speak."""
        print(f"  Speaking: {phrase}")
        if self.connected and self.robot:
            # TODO: Uncomment once SDK installed
            # self.robot.speak(phrase)
            pass

    def trigger_reaction(self, reaction_name):
        """Trigger a reaction."""
        if reaction_name not in REACTIONS:
            return

        reaction = REACTIONS[reaction_name]
        print(f"\n>>> {reaction_name.upper()}")

        if reaction.get("phrase"):
            self.speak(reaction["phrase"])

        self.play_motion(reaction["motion"])

    def run(self):
        """Main loop - listen for gamepad input."""
        if not self.connect_gamepad():
            return

        print("\n" + "=" * 50)
        print("ADAM REACTS (Gamepad) - Ready!")
        print("=" * 50)
        print("\nButton mappings:")
        for button, reaction in BUTTON_MAP.items():
            print(f"  Button {button} = {reaction}")
        print("\nPress Start/Menu to quit")
        print("-" * 50)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.JOYBUTTONDOWN:
                    button = event.button

                    # Quit on Start/Menu button (usually 7 or 9)
                    if button in [7, 9]:
                        running = False
                        break

                    # Trigger reaction
                    if button in BUTTON_MAP:
                        self.trigger_reaction(BUTTON_MAP[button])
                    else:
                        print(f"Unmapped button: {button}")

            time.sleep(0.01)  # Small delay to prevent CPU spin

        pygame.quit()
        print("\nGoodbye!")


def main():
    adam = AdamReactsGamepad(ROBOT_IP)
    adam.connect_robot()
    adam.run()


if __name__ == "__main__":
    main()
