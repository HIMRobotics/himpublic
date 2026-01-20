# Week 1: Adam Voice + Motion Test

**Goal:** Test ElevenLabs voice, validate a skill, and motion capture a football throw.

**Battery Warning:** You have ~30 minutes. Follow these steps in order!

---

## BEFORE You Go To The Robot (Laptop Prep)

Do all of this on your laptop BEFORE going to Adam.

### Step 1: Install Dependencies (5 min)

```bash
cd code
pip install -r requirements.txt
```

### Step 2: Set Up ElevenLabs API Key

1. Get your API key from: https://elevenlabs.io/app/settings/api-keys
2. Add to your shell:

```bash
# Add to ~/.zshrc or ~/.bashrc
export ELEVENLABS_API_KEY='your-key-here'

# Then reload
source ~/.zshrc
```

### Step 3: Generate Voice Files (2 min)

```bash
python voice_tts.py --generate
```

This creates MP3 files in `assets/audio/`. Verify they play:

```bash
python voice_tts.py --play assets/audio/greeting_1.mp3
```

### Step 4: Create Demo Motion (1 min)

```bash
python motion_capture.py demo
```

This creates a sample `football_throw.json` to test playback.

### Step 5: Install Booster SDK (10 min, one-time)

Only needed once. Run on the machine that will connect to Adam:

```bash
cd legacy/sdk

# Install C++ SDK
sudo ./install.sh

# Install Python bindings
pip install pybind11 pybind11-stubgen
mkdir -p build && cd build
cmake .. -DBUILD_PYTHON_BINDING=on
make
sudo make install
```

Verify SDK works:

```bash
python -c "import booster_robotics_sdk_python; print('SDK OK!')"
```

---

## 30-Minute Robot Session Checklist

**Bring:** Laptop with code ready, charged. USB cable if needed.

### Phase 1: Connect (5 min)

- [ ] Power on Adam
- [ ] Note Adam's IP address (usually on screen or `192.168.1.X`)
- [ ] Connect laptop to same network
- [ ] Test connection:

```bash
cd code
python quick_test.py --status
```

### Phase 2: Voice Test (5 min)

- [ ] Play pre-generated voice files:

```bash
python quick_test.py --voice
```

- [ ] Select option 1 to play `greeting_1.mp3`
- [ ] Verify audio plays through Adam's speaker
- [ ] Try a few different clips

**Troubleshooting:** If no sound, check volume or try `aplay` directly:
```bash
aplay ../assets/audio/greeting_1.mp3
```

### Phase 3: Skill Validation (5 min)

- [ ] Run skill test:

```bash
python quick_test.py --skill
```

- [ ] Select option 1 (Wave) - safe test
- [ ] Watch Adam wave
- [ ] Try option 2 (Head nod)
- [ ] If both work, skills are validated!

### Phase 4: Motion Capture - Football Throw (10 min)

- [ ] Enter custom mode:

```bash
python quick_test.py --skill
# Select option 4 (Custom mode)
```

- [ ] Adam's arms should now be manually movable
- [ ] Start recording:

```bash
python motion_capture.py record football_throw
```

- [ ] Position Adam's arm for "wind up" - press ENTER
- [ ] Position for "mid throw" - press ENTER  
- [ ] Position for "release" - press ENTER
- [ ] Position for "follow through" - press ENTER
- [ ] Type `done` to save

### Phase 5: Playback Test (5 min)

- [ ] Play back the recording:

```bash
python motion_capture.py playback football_throw --speed slow
```

- [ ] Watch Adam perform the throw
- [ ] If good, try `--speed medium`

### Phase 6: Real-time Voice Conversation (Optional, 10 min)

If time and battery permit, test the new real-time conversation system.

**Prerequisites:**
- [ ] Set up OpenAI API key:

```bash
# Add to ~/.zshrc or ~/.bashrc
export OPENAI_API_KEY='your-key-here'
source ~/.zshrc
```

**Audio Discovery:**
- [ ] Run audio discovery to find K1's audio interfaces:

```bash
python realtime_voice.py --discover
```

This will try to find ROS2 audio topics, SSH+ALSA, or fall back to local audio.

**Test Components Individually:**
- [ ] Test TTS (text-to-speech):

```bash
python realtime_voice.py --test-tts
```

- [ ] Test STT (speech-to-text):

```bash
python realtime_voice.py --test-stt
```

**Start Conversation:**
- [ ] Start talking to Adam:

```bash
python realtime_voice.py --talk
```

- [ ] Try saying sports-related things:
  - "Hey Adam!"
  - "I just scored a goal!"
  - "We lost the game today..."
  - "Let's play some basketball!"
- [ ] Say "bye" to end the conversation

**Troubleshooting:**
- If no audio output: Check `--discover` output for audio method
- If STT not working: Verify OPENAI_API_KEY is set
- If TTS not working: Verify ELEVENLABS_API_KEY is set

### Wrap Up

- [ ] Power off Adam (save battery!)
- [ ] Copy any recordings to safe location
- [ ] Note what worked and what didn't

---

## Quick Reference

### Files You Created

| File | Purpose |
|------|---------|
| `code/voice_tts.py` | Generate ElevenLabs voice audio |
| `code/motion_capture.py` | Record/playback arm motions |
| `code/quick_test.py` | All-in-one test menu |
| `code/realtime_voice.py` | Real-time voice conversation system |
| `code/k1_audio.py` | K1 speaker/microphone interface |
| `code/elevenlabs_stream.py` | Streaming TTS |
| `code/openai_stt.py` | Speech-to-text |
| `code/sports_responder.py` | GPT-4 sports personality |
| `assets/audio/` | Generated voice files |
| `assets/motions/` | Recorded motion JSON files |

### Key Commands

```bash
# Voice (Pre-recorded)
python voice_tts.py --generate      # Generate all preset phrases
python voice_tts.py --say "Hi!"     # Generate single phrase
python voice_tts.py --list          # List generated files

# Real-time Voice Conversation
python realtime_voice.py --discover     # Discover audio interfaces
python realtime_voice.py --talk         # Start conversation with Adam
python realtime_voice.py --test-tts     # Test text-to-speech
python realtime_voice.py --test-stt     # Test speech-to-text

# Motion
python motion_capture.py record NAME    # Record new motion
python motion_capture.py playback NAME  # Play back motion
python motion_capture.py list           # List recordings
python motion_capture.py demo           # Create demo (no robot)

# All-in-one
python quick_test.py                # Interactive menu
python quick_test.py --status       # Check system status
python quick_test.py --voice        # Jump to voice test
python quick_test.py --skill        # Jump to skill test
python quick_test.py --motion       # Jump to motion capture
```

---

## Troubleshooting

### SDK Import Error

```
ERROR: Booster SDK not installed!
```

Solution: Install the SDK (see Step 5 above).

### No Audio

1. Check file exists: `ls ../assets/audio/`
2. Try direct playback: `aplay FILE.mp3`
3. Check speaker volume on Adam

### Robot Not Responding

1. Check IP: `ping ROBOT_IP`
2. Check same network
3. Try restarting Adam

### Motion Capture Shows No Data

1. Make sure SDK is installed
2. Wait for state messages (up to 1 sec)
3. Check robot is in Custom mode

---

## End of Session Deliverables

- [ ] Voice files generated and tested
- [ ] At least one skill works (wave/head nod)
- [ ] Football throw motion captured
- [ ] Motion plays back correctly
- [ ] (Optional) Real-time voice conversation tested

---

## Notes

_Record what you learn here:_

```
Session Date:

Voice Test Results:

Skill Test Results:

Motion Capture Notes:

Issues Encountered:

Next Steps:
```
