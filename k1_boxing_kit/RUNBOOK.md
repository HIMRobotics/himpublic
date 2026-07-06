# K1 Boxing — Simple Runbook

Make Adam (Booster K1) throw punches with the remote controller.

**You need:** the K1 robot, the Booster remote, one person to hold/spot the robot,
and the Booster SDK installed on the robot.

---

## SAFETY — read this first (30 seconds)

- Keep people **out of arm's reach**. Punches are real arm motion.
- **Spot the robot** (hold it / have it supported) for the first runs.
- Start the robot in **DAMP mode** before you begin.
- Always run **slow** the first time (this kit defaults to slow).
- To stop instantly: press **Ctrl-C** in the terminal. The robot will go limp (damp).

The legs stay on the robot's own balance controller — this kit only moves the arms.

---

## Step 1 — Get the code on the robot

**If the robot already has this repo:** skip to Step 2.

**Otherwise, from your laptop** (in the `himpublic` folder):

```bash
cd k1_boxing_kit
./deploy.sh booster@<ROBOT-IP>
```

Replace `<ROBOT-IP>` with the robot's IP. (Ask whoever set up the robot, or check
the Booster app.)

---

## Step 2 — Log into the robot and go to the kit

```bash
ssh booster@<ROBOT-IP>
cd ~/k1_boxing_kit
```

---

## Step 3 — Check the joints move the right arms (no punching yet)

This is **read-only** — nothing moves on its own.

```bash
./run.sh verify
```

1. With the robot in DAMP, **gently move the LEFT arm by hand**.
2. Watch the numbers on screen. The `DEFAULT` line should change.
   - If the **`DEFAULT`** numbers change when you move the arms → you're good.
   - If only the **`MOTION_CAPTURE`** numbers change → open
     `k1_boxing/joints.py` and change the last line to:
     `K1_ARM_JOINT_INDICES = USE_MOTION_CAPTURE_INDICES`
3. Press **Ctrl-C** to stop.

---

## Step 4 — Box!

```bash
./run.sh fight
```

- Type `yes` at the safety prompt.
- **The robot will STAND UP and start balancing, then raise its fists.**
  Mode sequence: `DAMP → prepare → walking` (legs balance) + arm control on.
  **Keep hands on it for this part.**
- Use the **remote**:
  - **RT** = right punch
  - **LT** = left punch
  - **RB** = right uppercut
  - **A**  = block on/off
  - **B**  = victory pose
- Press **Ctrl-C** when done. It returns to guard, then **damps** the robot
  (goes limp/safe). Always exit this way.

### Robot modes (what they mean)
- **DAMP** = limp/safe, no stiffness. Start here; you end here.
- **prepare / walking** = robot is stiff and balancing on its legs. This kit only
  moves the **arms** while the legs balance themselves.

---

## If something looks wrong

- **A pose looks awkward / too far** → that's expected; poses were recorded on the
  T1. Stop (Ctrl-C). We'll re-tune for the K1 (see "Tuning" below).
- **"Booster SDK not installed"** → the SDK isn't built on this robot. Build it,
  then retry.
- **"No LowState received"** → wrong network interface. Try:
  `IFACE=<interface> ./run.sh verify`
- **Robot doesn't balance / drifts** → Ctrl-C immediately, put it back in DAMP.

---

## Tuning (optional, later)

Punch angles live in `k1_boxing/actions.py` as 8 numbers per frame:
`(L-shoulder-pitch, L-shoulder-roll, L-elbow-pitch, L-elbow-yaw, R-shoulder-pitch,
R-shoulder-roll, R-elbow-pitch, R-elbow-yaw)` in radians.

Easiest way to get K1-perfect poses: record them by hand with
`himpublic/code/motion_capture.py`, then paste the values into `actions.py`.

---

## What to report back

- Did `verify` show DEFAULT or MOTION_CAPTURE indices?
- Which punches looked good / bad?
- Any errors (copy the message).
