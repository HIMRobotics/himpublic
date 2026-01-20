#!/usr/bin/env python3
"""
Generate Audio Files for Adam's Reactions

Uses pyttsx3 for offline TTS or gTTS for Google's voices.
"""

import os
import sys

# Output directory
OUTPUT_DIR = "../assets/audio"

# Phrases to generate
PHRASES = {
    # Celebrate
    "celebrate_1.wav": "GOOOAL!",
    "celebrate_2.wav": "YES! What a play!",
    "celebrate_3.wav": "That's what I'm talking about!",
    "celebrate_4.wav": "Incredible!",

    # Disappointed
    "disappointed_1.wav": "Aww, so close!",
    "disappointed_2.wav": "Ohhh, unlucky!",
    "disappointed_3.wav": "Next time!",
    "disappointed_4.wav": "Almost had it!",

    # Greetings
    "greeting_1.wav": "Hey there!",
    "greeting_2.wav": "What's up!",
    "greeting_3.wav": "Good to see you!",
    "greeting_4.wav": "Hello friend!",

    # High-five
    "high_five_1.wav": "Up top!",
    "high_five_2.wav": "Nice one!",
    "high_five_3.wav": "Yeah!",
    "high_five_4.wav": "Awesome!",

    # General
    "intro.wav": "Hey, I'm Adam! Let's have some fun!",
    "goodbye.wav": "See you next time!",
}


def generate_with_pyttsx3():
    """Generate audio using pyttsx3 (offline)."""
    try:
        import pyttsx3
    except ImportError:
        print("pyttsx3 not installed. Run: pip install pyttsx3")
        return False

    engine = pyttsx3.init()

    # Adjust voice settings
    engine.setProperty('rate', 150)  # Speed
    engine.setProperty('volume', 1.0)  # Volume

    # List available voices
    voices = engine.getProperty('voices')
    print("Available voices:")
    for i, voice in enumerate(voices):
        print(f"  {i}: {voice.name}")

    # Use first voice (or change index)
    engine.setProperty('voice', voices[0].id)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename, phrase in PHRASES.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        print(f"Generating: {filename} -> '{phrase}'")
        engine.save_to_file(phrase, filepath)

    engine.runAndWait()
    print(f"\nGenerated {len(PHRASES)} audio files in {OUTPUT_DIR}")
    return True


def generate_with_gtts():
    """Generate audio using Google TTS (requires internet)."""
    try:
        from gtts import gTTS
    except ImportError:
        print("gTTS not installed. Run: pip install gtts")
        return False

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for filename, phrase in PHRASES.items():
        filepath = os.path.join(OUTPUT_DIR, filename)
        print(f"Generating: {filename} -> '{phrase}'")

        tts = gTTS(text=phrase, lang='en', slow=False)

        # gTTS outputs mp3, convert filename
        mp3_path = filepath.replace('.wav', '.mp3')
        tts.save(mp3_path)

    print(f"\nGenerated {len(PHRASES)} audio files in {OUTPUT_DIR}")
    print("Note: Files are MP3 format. Convert to WAV if needed.")
    return True


def main():
    print("=" * 50)
    print("AUDIO GENERATOR FOR ADAM")
    print("=" * 50)

    print("\nChoose TTS engine:")
    print("  1. pyttsx3 (offline, robotic voice)")
    print("  2. gTTS (Google, natural voice, needs internet)")

    choice = input("\nEnter choice (1 or 2): ").strip()

    if choice == "1":
        generate_with_pyttsx3()
    elif choice == "2":
        generate_with_gtts()
    else:
        print("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    main()
