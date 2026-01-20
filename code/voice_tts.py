#!/usr/bin/env python3
"""
Voice TTS - Generate realistic voice audio using ElevenLabs

Usage:
    python voice_tts.py              # Interactive menu
    python voice_tts.py --generate   # Generate all preset phrases
    python voice_tts.py --say "Hi!"  # Generate single phrase
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

# Output directory for audio files
OUTPUT_DIR = Path(__file__).parent.parent / "assets" / "audio"

# ElevenLabs voice ID - "Adam" voice (fitting!)
VOICE_ID = "pNInz6obpgDQGcFmaJgB"

# Model options: eleven_turbo_v2_5 (fast), eleven_multilingual_v2 (best quality)
MODEL_ID = "eleven_turbo_v2_5"

# Preset phrases for Adam
PHRASES = {
    # Greetings
    "greeting_1.mp3": "Hey there! I'm Adam!",
    "greeting_2.mp3": "What's up! Ready to have some fun?",
    "greeting_3.mp3": "Good to see you!",
    
    # Celebrate
    "celebrate_1.mp3": "GOOOAL!",
    "celebrate_2.mp3": "YES! What a play!",
    "celebrate_3.mp3": "That's what I'm talking about!",
    "celebrate_4.mp3": "Incredible!",
    
    # Disappointed
    "disappointed_1.mp3": "Aww, so close!",
    "disappointed_2.mp3": "Ohhh, unlucky!",
    "disappointed_3.mp3": "Next time!",
    
    # High-five
    "high_five_1.mp3": "Up top!",
    "high_five_2.mp3": "Nice one!",
    "high_five_3.mp3": "Yeah! Awesome!",
    
    # Football specific
    "football_1.mp3": "Go long!",
    "football_2.mp3": "Touchdown!",
    "football_3.mp3": "Nice catch!",
    
    # General
    "intro.mp3": "Hey, I'm Adam! Let's have some fun!",
    "goodbye.mp3": "See you next time!",
}


def get_elevenlabs_client():
    """Get ElevenLabs client, checking for API key."""
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        print("ERROR: elevenlabs not installed.")
        print("Run: pip install elevenlabs")
        sys.exit(1)
    
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY environment variable not set.")
        print("")
        print("Get your API key from: https://elevenlabs.io/app/settings/api-keys")
        print("Then run: export ELEVENLABS_API_KEY='your-key-here'")
        sys.exit(1)
    
    return ElevenLabs(api_key=api_key)


def generate_audio(text: str, filename: str, client=None) -> bool:
    """Generate audio file from text using ElevenLabs."""
    if client is None:
        client = get_elevenlabs_client()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = OUTPUT_DIR / filename
    
    print(f"Generating: {filename} -> '{text}'")
    
    try:
        audio = client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=text,
            model_id=MODEL_ID,
        )
        
        with open(filepath, "wb") as f:
            for chunk in audio:
                f.write(chunk)
        
        print(f"  Saved: {filepath}")
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def generate_all_phrases() -> None:
    """Generate all preset phrases."""
    print("=" * 50)
    print("GENERATING ALL PRESET PHRASES")
    print("=" * 50)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Voice ID: {VOICE_ID}")
    print(f"Total phrases: {len(PHRASES)}")
    print("")
    
    client = get_elevenlabs_client()
    success = 0
    failed = 0
    
    for filename, text in PHRASES.items():
        if generate_audio(text, filename, client):
            success += 1
        else:
            failed += 1
    
    print("")
    print(f"Done! Generated {success}/{len(PHRASES)} files.")
    if failed > 0:
        print(f"Failed: {failed}")


def generate_single(text: str, filename: Optional[str] = None) -> str:
    """Generate a single phrase, return filepath."""
    if filename is None:
        # Generate unique filename
        import hashlib
        hash_str = hashlib.md5(text.encode()).hexdigest()[:8]
        filename = f"custom_{hash_str}.mp3"
    
    client = get_elevenlabs_client()
    if generate_audio(text, filename, client):
        return str(OUTPUT_DIR / filename)
    return ""


def play_audio(filepath: str) -> None:
    """Play audio file using system player."""
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    print(f"Playing: {filepath}")
    
    # Try different players
    players = [
        ["aplay", filepath],           # Linux ALSA
        ["paplay", filepath],          # PulseAudio
        ["afplay", filepath],          # macOS
        ["mpv", "--no-video", filepath],  # Cross-platform
    ]
    
    for player in players:
        try:
            subprocess.run(player, check=True, capture_output=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
    
    print("No audio player found. Install aplay, paplay, or mpv.")


def list_generated_files() -> None:
    """List all generated audio files."""
    if not OUTPUT_DIR.exists():
        print("No audio files generated yet.")
        return
    
    files = list(OUTPUT_DIR.glob("*.mp3")) + list(OUTPUT_DIR.glob("*.wav"))
    if not files:
        print("No audio files found.")
        return
    
    print(f"\nGenerated audio files in {OUTPUT_DIR}:")
    for f in sorted(files):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name} ({size_kb:.1f} KB)")


def interactive_menu() -> None:
    """Interactive menu for voice generation."""
    print("=" * 50)
    print("ADAM VOICE GENERATOR (ElevenLabs)")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("  1. Generate all preset phrases")
        print("  2. Generate custom phrase")
        print("  3. Play an audio file")
        print("  4. List generated files")
        print("  Q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == "1":
            generate_all_phrases()
        
        elif choice == "2":
            text = input("Enter phrase: ").strip()
            if text:
                filepath = generate_single(text)
                if filepath:
                    play_choice = input("Play it? (y/n): ").strip().lower()
                    if play_choice == "y":
                        play_audio(filepath)
        
        elif choice == "3":
            list_generated_files()
            filename = input("Enter filename to play: ").strip()
            if filename:
                filepath = OUTPUT_DIR / filename
                play_audio(str(filepath))
        
        elif choice == "4":
            list_generated_files()
        
        elif choice == "q":
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate voice audio with ElevenLabs")
    parser.add_argument("--generate", action="store_true", help="Generate all preset phrases")
    parser.add_argument("--say", type=str, help="Generate a single phrase")
    parser.add_argument("--play", type=str, help="Play an audio file")
    parser.add_argument("--list", action="store_true", help="List generated files")
    
    args = parser.parse_args()
    
    if args.generate:
        generate_all_phrases()
    elif args.say:
        filepath = generate_single(args.say)
        if filepath:
            play_audio(filepath)
    elif args.play:
        play_audio(args.play)
    elif args.list:
        list_generated_files()
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
