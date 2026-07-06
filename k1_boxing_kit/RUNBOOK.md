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

## Step 0 — Test the connection first (SSH + IP)

Do this before anything else. Nothing on the robot moves here.

**Wired (Ethernet) — recommended for the demo:**
- Robot IP is `192.168.10.102`.
- Set your laptop's wired network to a static IP: address `192.168.10.10`,
  netmask `255.255.255.0`, gateway `192.168.10.1`.

**Wi-Fi:** the IP is whatever the network assigns — find it in the Booster app.
Use that IP below instead of `192.168.10.102`.

Then from your laptop:

```bash
ping 192.168.10.102              # should get replies (Ctrl-C to stop)
ssh booster@192.168.10.102       # password: 123456
```

If SSH logs you in, you're good — type `exit` and continue to Step 1.

**If it fails:**
- `Request timeout` / no ping → wrong IP, cable not seated, or laptop not on the
  `192.168.10.x` subnet (re-check the static IP above). On Wi-Fi, re-check the app.
- `Permission denied` → wrong password (default is `123456`).
- `Connection refused` → robot still booting; wait ~30s and retry.

---

## Step 1 — Get the code on the robot

**If the robot already has this repo:** skip to Step 2.

**Otherwise, from your laptop** (in the `himpublic` folder):

```bash
cd k1_boxing_kit
./deploy.sh booster@192.168.10.102
```

(Use the Wi-Fi IP from the app instead of `192.168.10.102` if you're not on
Ethernet.)

---

## Step 2 — Log into the robot and go to the kit

```bash
ssh booster@192.168.10.102        # password: 123456
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
  T1. Stop (Ctrl-C) and use the **Backup plan** below to record K1 poses by hand.
- **"Booster SDK not installed"** → the SDK isn't built on this robot. Build it,
  then retry.
- **"No LowState received"** → wrong network interface. Try:
  `IFACE=<interface> ./run.sh verify`
- **Robot doesn't balance / drifts** → Ctrl-C immediately, put it back in DAMP.

---

## BACKUP PLAN — if the punches look wrong on the K1

The punches were recorded on the T1. If a pose is off (arm too far, awkward angle),
record K1-native poses by hand. **This is read-only and safe — the robot stays in
DAMP (limp), nothing is driven.**

1. Put the robot in **DAMP** (limp).
2. Record a punch, one keyframe at a time:

```bash
./run.sh capture LEFT_PUNCH
```

3. Move the arms by hand to each position and press **ENTER** to snapshot.
   Do a few frames (start pose → mid → extended → back). Type `done` when finished.
4. It prints a `LEFT_PUNCH = [ ... ]` block. **Copy it into `k1_boxing/actions.py`**,
   replacing the matching sequence (put it above the `_as_dicts` section near the
   bottom). Names you can record: `LEFT_PUNCH`, `RIGHT_PUNCH`, `RIGHT_UPPERCUT`,
   `FIGHT_POSE_TO_BLOCK`, `BLOCK_TO_FIGHT_POSE`, `VICTORY_ANIMATION`.
5. Re-run `./run.sh fight`.

Reference — each frame is 8 numbers (radians):
`(L-shoulder-pitch, L-shoulder-roll, L-elbow-pitch, L-elbow-yaw, R-shoulder-pitch,
R-shoulder-roll, R-elbow-pitch, R-elbow-yaw)`.

---

## What to report back

- Did `verify` show DEFAULT or MOTION_CAPTURE indices?
- Which punches looked good / bad?
- Any errors (copy the message).
