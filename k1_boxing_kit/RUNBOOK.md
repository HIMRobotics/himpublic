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

**Before the real demo, run the [Pre-Demo Rehearsal](#pre-demo-rehearsal-do-this-once-before-the-real-demo)**
— record the K1 punches and do a full power-cycle test of the no-laptop flow.

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

**Stand Adam up first** (press **STAND** then **WLAK** on his back panel, or use the
app) so he's upright and balancing. Then run:

```bash
./run.sh fight-standing
```

This is the normal command — it assumes he's already standing and just turns on arm
control (it does NOT try to re-stand him).

- Type `yes` at the safety prompt.
- He takes the **guard stance**, then you box with the **remote** (face buttons +
  D-pad — the triggers/bumpers often don't register on this controller):
  - **Y** = right punch   (RT also, if it works)
  - **X** = left punch    (LT also, if it works)
  - **B** = right uppercut (RB also, if it works)
  - **A** = block (quick guard-up, then back)
  - **D-pad Up** = victory pose
- Press **Ctrl-C** when done. It returns to guard, then leaves him **standing in
  ready mode (not limp)**. Always exit this way. (Add `--damp-on-exit` only if he's
  supported and you want him to go limp instead.)

> Not standing him yourself? `./run.sh fight` will try to stand him up
> (`DAMP → prepare → walking`) — but many robots only stand from the physical
> buttons, so `fight-standing` above is the reliable path.

### Robot modes (what they mean)
- **DAMP** = limp, no stiffness. Start here. (Ctrl-C no longer ends in DAMP.)
- **prepare / walking** = robot is stiff and balancing on its legs. This kit only
  moves the **arms** while the legs balance themselves.

---

## Demo without a laptop (no SSH each time)

**Level 1 — SSH once, then leave it running.** Start `./run.sh fight-standing` at the
beginning of the demo and just leave the terminal open. The remote does everything
after that; you don't touch the laptop again until you're done.

**Level 2 — Autostart service (never need the laptop after setup).** Install once:

```bash
# on the robot, one time:
cd ~/himpublic/k1_boxing_kit
./install-service.sh
```

**This is safe and fully reversible.** It only adds ONE file
(`/etc/systemd/system/k1-boxing.service`) and does **not** touch any of Booster's own
code or config. It runs a background **listener that does nothing** until you press a
button combo — the robot behaves 100% normally until then. It will **not**
auto-restart/loop if something goes wrong (it just stops).

After that, for every demo (NO laptop, NO SSH):
1. Power on Adam, wait for the boot tone.
2. Stand him up: **LT+START** (or STAND button), then **RT+A** (or WLAK button).
3. **Press START + BACK on the remote to START boxing.** He takes the guard stance;
   now Y/X/B/A/D-pad-up throw punches.
4. **Press START + BACK again to STOP boxing.** Arms release and the robot is back to
   normal — all his other functions work again.

You can toggle boxing on/off as many times as you want with START+BACK. When it's
OFF, nothing about the robot is affected.

> If START+BACK doesn't toggle on your remote, tell us — it's a one-line change in
> `k1_boxing/state_machine.py` (`TOGGLE_BUTTONS`).

### Kill it / remove it (save these)
- **Stop right now:** on the controller press **LT + BACK** (DAMP) or the **F1**
  button. That makes him safe instantly.
- **Stop the service:** `sudo systemctl stop k1-boxing`
- **Never start on boot again:** `sudo systemctl disable k1-boxing`
- **REMOVE IT COMPLETELY (one command):**
  ```bash
  ./uninstall-service.sh
  ```
  This stops it, disables it, and deletes the one file — the robot is back exactly as
  before. You can still run boxing manually anytime with `./run.sh fight-standing`.
- **Watch what it's doing:** `journalctl -u k1-boxing -f`

> Nervous about it for the demo? Skip Level 2 entirely and just use **Level 1**
> (SSH once, run `./run.sh fight-standing`, leave it open). Same result, nothing
> installed on the robot.

---

## Pre-Demo Rehearsal (do this once before the real demo)

Two parts. Part 1 makes the punches look good on the K1. Part 2 rehearses the exact
laptop-free flow you'll use at the demo, from a cold power-on.

### Part 1 — Record the punches + test (with SSH, spotter on)
1. SSH in and get the latest code:
   ```bash
   ssh booster@<ROBOT-IP>
   cd ~/himpublic && git pull && cd k1_boxing_kit
   ```
2. `./run.sh check` — confirm data link + remote are OK.
3. Record K1 punches (see **Appendix A**). Do at least `RIGHT_PUNCH`, `LEFT_PUNCH`,
   `RIGHT_UPPERCUT` (add block + victory if you want). Paste each into `actions.py`.
4. Stand him up: **LT+START**, then **RT+A**.
5. `./run.sh fight-standing` and test **every** button (Y / X / B / A / D-pad up).
   Tune poses until they look good. Ctrl-C when happy.

### Part 2 — Full power-cycle rehearsal (exactly like the demo, NO laptop)
1. Install the autostart service once (if not already): `./install-service.sh`.
2. **Power Adam fully OFF, then ON** — pretend you just arrived at the demo.
3. Wait ~1 min for the boot tone. **Do not touch the laptop from here.**
4. Put the controller in receiver mode (3 solid LEDs). Stand him: **LT+START**,
   then **RT+A**.
5. Press **START + BACK** → boxing turns on (guard stance). Throw a few punches.
6. Press **START + BACK** → boxing off; check his normal functions still work.
7. Power cycle one more time and repeat 3–6 to be sure it's repeatable.

If Part 2 works with the laptop closed, you're demo-ready. If any step fails, that's
the exact thing to fix — and you can always fall back to **Level 1** (SSH once, run
`./run.sh fight-standing`, leave it open).

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
- **A pose looks awkward / too far** → expected; poses were recorded on the T1.
  Re-record them on the K1 — see **Appendix A — Record K1 punches**.
- **"Booster SDK not installed"** → the SDK isn't built on this robot. Build it,
  then retry.
- **"No LowState received"** → wrong network interface. Try:
  `IFACE=<interface> ./run.sh verify`
- **Robot doesn't balance / drifts** → Ctrl-C immediately, put it back in DAMP.

---

## What to report back

- Did `verify` show DEFAULT or MOTION_CAPTURE indices?
- Which punches looked good / bad?
- Any errors (copy the message).

---

## Appendix A — Record K1 punches (recommended)

The built-in punches were recorded on the **T1**, so they look off on the K1. Record
K1-native poses by hand. **This is read-only and safe — the robot stays in DAMP
(limp), nothing is driven while recording.**

1. Put the robot in **DAMP** (limp).
2. Record a punch, one keyframe at a time:

```bash
./run.sh capture RIGHT_PUNCH
```

3. Move the arms by hand to each position and press **ENTER** to snapshot.
   Do a few frames (guard → mid → extended → back). Type `done` when finished.
4. It prints a `RIGHT_PUNCH = [ ... ]` block. **Copy it into `k1_boxing/actions.py`**,
   replacing the matching sequence (put it above the `_as_dicts` section near the
   bottom).
5. Repeat for the moves you want. Names to record:
   `RIGHT_PUNCH`, `LEFT_PUNCH`, `RIGHT_UPPERCUT`, `FIGHT_POSE_TO_BLOCK`,
   `BLOCK_TO_FIGHT_POSE`, `VICTORY_ANIMATION`.
6. Test: stand him up, then `./run.sh fight-standing`.

Reference — each frame is 8 numbers (radians):
`(L-shoulder-pitch, L-shoulder-roll, L-elbow-pitch, L-elbow-yaw, R-shoulder-pitch,
R-shoulder-roll, R-elbow-pitch, R-elbow-yaw)`.

> Tip: `FIGHT_POSE_TO_BLOCK` and `BLOCK_TO_FIGHT_POSE` are reverses of each other —
> record the block, then enter the same frames in reverse for the recovery.

---

## Appendix B — copy from laptop instead (only if robot has no internet)

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
