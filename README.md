# Adam Development

> **Note:** This repo was vibe coded - it's a collection of experiments with Adam, our Booster K1 humanoid robot. Code quality varies, things might break, and that's okay. We're learning as we go.

Development folder for Adam's sports skills and social media presence.

## What is this?

We're teaching a humanoid robot to have personality - react to sports, wave at people, dance, and generally be fun. This repo contains all our experiments, scripts, and learnings.

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/HIMRobotics/bordeaux.git
cd bordeaux
pip install -r code/requirements.txt
```

### 2. Set up API keys

You'll need API keys for voice features:

```bash
# Add to ~/.zshrc or ~/.bashrc
export ELEVENLABS_API_KEY='your-key-here'  # For realistic TTS
export OPENAI_API_KEY='your-key-here'      # For real-time voice chat
```

Get keys from:
- ElevenLabs: https://elevenlabs.io/app/settings/api-keys
- OpenAI: https://platform.openai.com/api-keys

### 3. Install Booster SDK (for robot control)

See `week1/plan.md` for full instructions, or:

```bash
cd legacy/sdk
sudo ./install.sh
pip install pybind11 pybind11-stubgen
mkdir -p build && cd build
cmake .. -DBUILD_PYTHON_BINDING=on
make && sudo make install
```

## Folder Structure

```
├── code/           # Python scripts (the good stuff)
├── assets/         # Audio files, motion data
├── legacy/         # SDK, utilities, Jupyter notebooks
├── week1/          # Setup guide + first experiments
├── week2/          # Reaction system build
└── week3/          # Content creation notes
```

## Quick Start

```bash
# Test robot connection
python code/test_connection.py

# Run the reaction system
python code/adam_reacts.py

# Test voice generation
python code/voice_tts.py --generate
```

## Key Scripts

| Script | What it does |
|--------|--------------|
| `adam_reacts.py` | Main reaction system - press keys to trigger reactions |
| `realtime_voice.py` | Real-time voice conversation with Adam |
| `voice_tts.py` | Generate voice clips with ElevenLabs |
| `motion_capture.py` | Record and playback arm motions |
| `quick_test.py` | All-in-one test menu |

## The Goal

**Make Adam have personality.**

5 core reactions -> film -> post -> see what resonates -> iterate.

## Related Repos

- [booster_robotics_sdk](https://github.com/BoosterRobotics/booster_robotics_sdk) - Official Booster SDK
- [robocup_demo](https://github.com/BoosterRobotics/robocup_demo) - Soccer demos
- [GMR](https://github.com/YanjieZe/GMR) - Motion retargeting for custom dances

## Contributing

This is experimental code, but PRs are welcome! If something's broken, open an issue.

## License

MIT - see [LICENSE](LICENSE)
