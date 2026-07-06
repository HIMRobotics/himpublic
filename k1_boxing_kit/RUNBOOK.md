# K1 Boxing — Simple Runbook

Make Adam (Booster K1) throw punches with the remote controller.

**You need:** the K1 robot, the Booster remote, one person to hold/spot the robot,
and the Booster SDK installed on the robot.

---

## TL;DR — just do this (on the robot)

```bash
ssh booster@<ROBOT-IP>                 # password: 123456  (find IP: Booster app)
git clone https://github.com/HIMRobotics/himpublic.git   # or: cd himpublic && git pull
cd himpublic/k1_boxing_kit

./run.sh check          # 1) confirms link + remote are working (nothing moves)
./run.sh verify         # 2) confirm arm joints (move arms by hand)
# stand Adam: press STAND then WLAK on his back panel
./run.sh fight-standing # 3) box! Y=right punch X=left punch B=uppercut A=block Dpad-up=victory
```

Ctrl-C anytime = stop (he returns to guard and stays standing in ready mode).
If a step fails, it prints what to fix.
Full detail + troubleshooting below.

---

## SAFETY — read this first (30 seconds)

- Keep people **out of arm's reach**. Punches are real arm motion.
- **Spot the robot** (hold it / have it supported) for the first runs.
- Start the robot in **DAMP mode** before you begin.
- Always run **slow** the first time (this kit defaults to slow).
- To stop: press **Ctrl-C**. He returns to guard and **stays standing (ready mode),
  not limp**. For an EMERGENCY limp, press **LT + BACK** on the controller, or the
  **F1** button on his back panel.

The legs stay on the robot's own balance controller — this kit only moves the arms.

---

## Step 0 — Find the robot's IP and test the connection

Do this before anything else. Nothing on the robot moves here.
Everywhere below, replace `<ROBOT-IP>` with Adam's real IP.

### Find `<ROBOT-IP>`
Try these in order — the app is easiest:

1. **Booster app (best):** connect to the robot, open the control/settings page —
   it shows the robot's current IP.
2. **Scan from your laptop** (same network):
   ```bash
   arp -a                      # look for the robot entry
   # or, if you have nmap (use YOUR subnet):
   nmap -sn 192.168.1.0/24
   ```
3. **Wired default (only if you set up the static Ethernet link):** `192.168.10.102`
   with your laptop at static IP `192.168.10.10` / `255.255.255.0` / gw `192.168.10.1`.
   (This is just Booster's default — it is probably NOT your Wi-Fi IP.)

### Test it
```bash
ping <ROBOT-IP>                 # should get replies (Ctrl-C to stop)
ssh booster@<ROBOT-IP>          # password: 123456 (won't show as you type)
```

If SSH logs you in, you're good — continue to Step 1 (you're already on the robot).

**If it fails:**
- `Request timeout` / no ping → wrong IP, or laptop and robot are on different
  networks. Re-check the IP (the app is the source of truth).
- `Permission denied` → wrong password (default is `123456`).
- `Connection refused` → robot still booting; wait ~30s and retry.

---

## Step 1 — Get the code onto the robot (SIMPLEST WAY)

Log into the robot, then clone the repo **on the robot** (pull straight from GitHub
onto Adam). No copying from the laptop, no scp.

```bash
ssh booster@<ROBOT-IP>            # password: 123456 (won't show as you type)
```

Now you're ON the robot. Get the code:

```bash
git clone https://github.com/HIMRobotics/himpublic.git
cd himpublic/k1_boxing_kit
```

Already cloned before? Just update it instead:

```bash
cd ~/himpublic && git pull && cd k1_boxing_kit
```

That's it — go to Step 2.

> Don't use `deploy.sh` unless the robot has **no internet**. `scp` is what was
> hanging on you. If you must copy from the laptop, see the Appendix at the bottom.

---

## Step 2 — Check the joints move the right arms (no punching yet)

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

## Step 2.5 — Connect the controller (do this if Adam ignores the remote)

Adam listens to the Booster (XBOX-compatible) joystick. If he's not responding to it
**at all**, it's almost always one of these — from Booster's own manual:

1. **Controller must be in RECEIVER MODE — 3 LEDs solid ON.** This is Booster's
   requirement. If you don't see 3 solid LEDs, it is NOT connected to the robot.
   Power the controller on and put it in receiver mode (cycle its mode button until
   the 3 LEDs are solid), per the controller's instructions.
2. **Robot must be fully booted.** After power-on, wait ~1 minute until it plays the
   prompt tone. It won't respond to the controller before that.

### Prove the controller talks to the robot (Booster's built-in test)
Press **LT + START** on the joystick.
- **Adam stiffens into a ready posture (PREP mode)** → the controller IS connected.
  You're good — go to Step 3.
- **Nothing happens** → the controller is NOT connected. Fix receiver mode (3 LEDs)
  and make sure he's booted, then try again.

Handy built-in button combos (from Booster):
- **LT + START** → PREP (ready / stand) mode
- **RT + A** → WALK mode (only once he's standing in PREP)
- **LT + BACK** → DAMP (limp)

### Then confirm our software sees the buttons too
```bash
./run.sh remote        # press buttons; lines should appear. Ctrl-C when done.
```
- **Lines appear** → great, boxing will get your button presses.
- **Nothing appears even though LT+START worked** → tell us; we may need to point the
  code at a different remote channel.

> Note: while Adam runs his built-in program, some single buttons (like **A**) may
> also trigger a default action (e.g. handshake). If a button does something
> unexpected, tell us which button and we'll remap the punches.

---

## Step 3 — Box!

```bash
./run.sh fight
```

- Type `yes` at the safety prompt.
- **The robot will STAND UP and start balancing, then raise its fists.**
  Mode sequence: `DAMP → prepare → walking` (legs balance) + arm control on.
  **Keep hands on it for this part.**
- Use the **remote** (face buttons + D-pad — the triggers/bumpers often don't
  register on this controller, so we use the buttons that do):
  - **Y** = right punch   (RT also, if it works)
  - **X** = left punch    (LT also, if it works)
  - **B** = right uppercut (RB also, if it works)
  - **A** = block on/off
  - **D-pad Up** = victory pose
- Press **Ctrl-C** when done. It returns to guard, then leaves him **standing in
  ready mode (not limp)**. Always exit this way. (Add `--damp-on-exit` only if he's
  supported and you want him to go limp instead.)

### Robot modes (what they mean)
- **DAMP** = limp, no stiffness. Start here. (Ctrl-C no longer ends in DAMP.)
- **prepare / walking** = robot is stiff and balancing on its legs. This kit only
  moves the **arms** while the legs balance themselves.

---

## If something looks wrong

- **He's NOT standing when you start fight mode** → the SDK stand-up was likely
  refused (the robot often only stands from the physical buttons). Do this instead:
  1. Ctrl-C to stop.
  2. On Adam's **back panel**, press **STAND** (ready), then **WLAK** (walking).
     He should be upright and balancing. (Or stand him via the Booster app.)
  3. Now run the "already standing" version — it skips the auto stand-up and just
     turns on arm control:
     ```bash
     ./run.sh fight-standing
     ```
  Watch the log lines: `kPrepare: OK/FAILED`, `kWalking: OK/FAILED`, and
  `Current robot mode: ...` tell you exactly what the robot accepted.
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

---

## Appendix — copy from laptop instead (only if robot has no internet)

Prefer Step 1 (clone on the robot). Use this only if the robot can't reach GitHub.

From your **laptop**, in the `himpublic/k1_boxing_kit` folder:

```bash
./deploy.sh booster@<ROBOT-IP>
```

`scp` will ask for the robot password (`123456`) — it won't show as you type.

**If it hangs with no password prompt at all**, the laptop can't reach the robot
(not a password problem). Fix the connection first with Step 0's `ping` test, then
retry. As a one-time key setup to avoid password prompts entirely:

```bash
ssh-copy-id booster@<ROBOT-IP>   # type 123456 once; future connects are passwordless
```
