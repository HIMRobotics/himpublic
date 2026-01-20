#!/usr/bin/env python3
"""
Adam Reacts - Main reaction control script

Trigger reactions via keyboard/numpad:
  1 = Celebrate (goal/win)
  2 = Disappointed (miss/loss)
  3 = Wave (greeting)
  4 = Dance (timeout/halftime)
  5 = High-five (interaction)

  Q = Quit
"""

import time
import sys
import os

# TODO: Uncomment once SDK is installed
# from booster_robotics_sdk import Robot

# ============================================
# CONFIGURATION - UPDATE THESE
# ============================================
ROBOT_IP = "192.168.1.100"  # Replace with your robot's IP
AUDIO_DIR = "../assets/audio"  # Path to audio files
# ============================================


# Define reactions: (motion_name, audio_file, phrase_for_tts)
REACTIONS = {
    "1": {
        "name": "celebrate",
        "motion": "celebrate",  # Built-in motion name
        "audio": "celebrate.wav",
        "phrase": "GOOOAL!",
    },
    "2": {
        "name": "disappointed",
        "motion": "sad_pose",
        "audio": "disappointed.wav",
        "phrase": "Aww, so close!",
    },
    "3": {
        "name": "wave",
        "motion": "wave",
        "audio": "greeting.wav",
        "phrase": "Hey there!",
    },
    "4": {
        "name": "dance",
        "motion": "dance",
        "audio": None,  # Play music instead
        "phrase": None,
    },
    "5": {
        "name": "high_five",
        "motion": "high_five",
        "audio": "high_five.wav",
        "phrase": "Up top!",
    },
}


class AdamReacts:
    def __init__(self, robot_ip):
        self.robot_ip = robot_ip
        self.robot = None
        self.connected = False

    def connect(self):
        """Connect to the robot."""
        print(f"Connecting to robot at {self.robot_ip}...")
        try:
            # TODO: Uncomment once SDK installed
            # self.robot = Robot(self.robot_ip)
            # self.robot.connect()
            # self.connected = True
            print("Robot connection placeholder - SDK not installed yet")
            self.connected = False  # Change to True when SDK works
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False
        return self.connected

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

    def play_audio(self, audio_file):
        """Play an audio file."""
        audio_path = os.path.join(AUDIO_DIR, audio_file)
        print(f"  Playing audio: {audio_path}")
        # TODO: Implement audio playback
        # Could use pygame, simpleaudio, or robot's built-in speaker

    def trigger_reaction(self, key):
        """Trigger a reaction based on key press."""
        if key not in REACTIONS:
            return False

        reaction = REACTIONS[key]
        print(f"\n>>> Triggering: {reaction['name'].upper()}")

        # Play audio or speak phrase
        if reaction.get("audio"):
            self.play_audio(reaction["audio"])
        elif reaction.get("phrase"):
            self.speak(reaction["phrase"])

        # Play motion
        self.play_motion(reaction["motion"])

        return True

    def run(self):
        """Main loop - listen for key presses."""
        print("\n" + "=" * 50)
        print("ADAM REACTS - Ready!")
        print("=" * 50)
        print("\nPress keys to trigger reactions:")
        print("  1 = Celebrate")
        print("  2 = Disappointed")
        print("  3 = Wave")
        print("  4 = Dance")
        print("  5 = High-five")
        print("  Q = Quit")
        print("\n" + "-" * 50)

        try:
            while True:
                key = input("\nPress key: ").strip().lower()

                if key == "q":
                    print("Goodbye!")
                    break

                if not self.trigger_reaction(key):
                    print(f"Unknown key: {key}")

        except KeyboardInterrupt:
            print("\n\nExiting...")


def main():
    adam = AdamReacts(ROBOT_IP)

    # Try to connect (will work once SDK is installed)
    adam.connect()

    # Run the main loop
    adam.run()


if __name__ == "__main__":
    main()
