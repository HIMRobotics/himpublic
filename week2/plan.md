# Week 2: Adam Reacts

**Goal:** Build the reaction system - triggers + motions + voice

---

## Day 1: Set Up Trigger System

### Option A: USB Numpad (Recommended)
Cheap, reliable, no coding needed for input.

```bash
# Test numpad detection
sudo apt install evtest
evtest  # Select your numpad, press keys to see events
```

### Option B: Gamepad
Xbox/PS controller for more buttons.

```bash
pip install pygame
python ../code/test_gamepad.py
```

### Option C: Voice (Advanced)
Use built-in Booster ASR or add whisper.

---

## Day 2: Map Reactions

### The 5 Core Reactions

| Key | Reaction | Motion | Phrase |
|-----|----------|--------|--------|
| 1 | Celebrate | celebrate/dance | "GOOOAL!" |
| 2 | Disappointed | sad_pose | "Aww, so close!" |
| 3 | Wave | wave | "Hey there!" |
| 4 | Dance | dance_routine | (music plays) |
| 5 | High-five | high_five | "Up top!" |

### Test Each Reaction
```bash
python ../code/adam_reacts.py
# Press 1-5 to trigger reactions
```

---

## Day 3: Record Voice Lines

### Phrases to Record
Using TTS or record real voice:

1. **Celebrate**
   - "GOOOAL!"
   - "YES! What a play!"
   - "That's what I'm talking about!"

2. **Disappointed**
   - "Aww, so close!"
   - "Ohhh, unlucky!"
   - "Next time!"

3. **Greetings**
   - "Hey there!"
   - "What's up!"
   - "Good to see you!"

4. **High-five**
   - "Up top!"
   - "Nice one!"
   - "Yeah!"

### Generate with TTS
```bash
python ../code/generate_audio.py
```

---

## Day 4: Add Custom Motions (Optional)

### Using GMR for Custom Dances
```bash
# Clone GMR in a directory of your choice
git clone https://github.com/YanjieZe/GMR.git
cd GMR
pip install -r requirements.txt
```

### Retarget a Dance
```bash
# Download dance BVH from LAFAN1 or record your own
python retarget.py --robot booster_k1 --input dance.bvh --output ../assets/custom_dance.json
```

---

## Day 5: Integration Test

### Full System Test
1. Power on robot
2. Run `adam_reacts.py`
3. Have someone trigger reactions while you film
4. Review footage

### Event Simulation
Practice the full workflow:
1. "Someone scores" → Press 1 → Adam celebrates
2. "Someone approaches" → Press 3 → Adam waves
3. "Timeout" → Press 4 → Adam dances

---

## End of Week 2 Deliverables

- [ ] Trigger system working (numpad/gamepad/voice)
- [ ] 5 reactions mapped and tested
- [ ] Voice lines recorded/generated
- [ ] Full system runs smoothly
- [ ] Practice footage filmed

---

## Notes

_Use this space to document what you learn this week_

```
Day 1:

Day 2:

Day 3:

Day 4:

Day 5:
```
