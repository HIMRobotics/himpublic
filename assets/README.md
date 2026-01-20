# Assets

Store motion files, audio, and other assets here.

## Structure

```
assets/
├── audio/          # Voice lines (generate with code/voice_tts.py)
├── motions/        # Custom motion files (JSON from motion_capture.py)
└── music/          # Background music for dances
```

## Generating Audio (ElevenLabs)

```bash
cd ../code

# Set your API key first
export ELEVENLABS_API_KEY='your-key-here'

# Generate all preset phrases
python voice_tts.py --generate

# Or generate a single phrase
python voice_tts.py --say "Hello world!"

# List generated files
python voice_tts.py --list
```

This will create voice files in `audio/`.

## Recording Motions

```bash
cd ../code

# Record a new motion (requires robot connection)
python motion_capture.py record football_throw

# Create a demo motion (no robot needed)
python motion_capture.py demo

# Play back a recorded motion
python motion_capture.py playback football_throw --speed slow

# List all recordings
python motion_capture.py list
```

Motion files are saved as JSON in `motions/`.

## Getting Motion Data

### Built-in Booster Actions
The robot comes with built-in actions. List them:
```python
from booster_robotics_sdk import Robot
robot = Robot("IP")
robot.connect()
print(robot.list_actions())
```

### Manual Motion Capture
Use `motion_capture.py` to record by physically positioning Adam's arms:
1. Put robot in Custom mode
2. Position arms for each keyframe
3. Press ENTER to record each position
4. Type 'done' to save

### Custom Motions via GMR (Advanced)
```bash
# Clone GMR
git clone https://github.com/YanjieZe/GMR.git

# Retarget a dance
python GMR/retarget.py --robot booster_k1 --input dance.bvh --output motions/custom_dance.json
```

### Motion Data Sources
- **LAFAN1** - Dance and athletic motions (free)
- **AMASS** - Large motion database (academic)
- **Mixamo** - Free character animations (convert to BVH)
