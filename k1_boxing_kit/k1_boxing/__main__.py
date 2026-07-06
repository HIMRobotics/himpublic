"""K1 Boxing entry point.

    python3 -m k1_boxing --verify-joints        # confirm arm indices (no motion)
    python3 -m k1_boxing --speed slow           # remote-controlled fight mode

SAFETY:
  - Start the robot in DAMP mode, with a spotter, supported for the first runs.
  - Fight mode keeps the legs on the balance controller (kWalking) and only drives
    the arms via UpperBodyCustomControl.
  - Poses were recorded on the T1; run --speed slow and re-tune on the K1.
  - ALWAYS exit cleanly (Ctrl-C) so the remote subscriber is torn down.
"""

import argparse
import logging
import signal
import threading
import time

from .lib import BoosterLowLevelController
from .state_machine import FightingStateMachine, RemoteTriggeredController
from .joints import DEFAULT_INDICES, USE_MOTION_CAPTURE_INDICES, ARM_JOINT_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("k1_boxing")


def _confirm(skip: bool) -> bool:
    if skip:
        return True
    print("\n" + "!" * 60)
    print("K1 BOXING - SAFETY CHECK")
    print("!" * 60)
    print("Confirm ALL of the following before continuing:")
    print("  [ ] Robot started in DAMP mode")
    print("  [ ] Spotter present; robot supported for first runs")
    print("  [ ] Clear space around the arms")
    print("  [ ] Running --speed slow the first time")
    try:
        return input("\nType 'yes' to proceed: ").strip().lower() == "yes"
    except (EOFError, KeyboardInterrupt):
        return False


def _doctor(robot: BoosterLowLevelController) -> None:
    """One-shot health check: data link, mode, and remote. Read-only, no motion."""
    print("\n" + "=" * 60)
    print("K1 BOXING - SYSTEM CHECK  (nothing moves)")
    print("=" * 60)
    all_ok = True

    # 1) Data link to the robot
    print("\n1) Robot data link...")
    try:
        robot.read_low_state_values([0], timeout_s=5.0)
        print("   PASS - receiving state from the robot.")
    except Exception as exc:
        all_ok = False
        print(f"   FAIL - {exc}")
        print("   -> Robot powered on? Control service running? Right IP/interface?")

    # 2) Current mode
    print("\n2) Current robot mode:")
    robot.log_current_mode()

    # 3) Remote controller
    print("\n3) Remote controller - PRESS ANY BUTTON now (6 seconds)...")
    seen = {"n": 0}
    sub = None
    try:
        from booster_robotics_sdk_python import B1RemoteControllerStateSubscriber

        def on_rc(rc):
            try:
                if rc.event:
                    seen["n"] += 1
            except Exception:
                pass

        sub = B1RemoteControllerStateSubscriber(on_rc)
        sub.InitChannel()
        time.sleep(6)
    except Exception as exc:
        print(f"   (remote check error: {exc})")
    finally:
        if sub is not None:
            try:
                sub.CloseChannel()
            except Exception:
                pass

    if seen["n"] > 0:
        print(f"   PASS - saw {seen['n']} remote inputs.")
    else:
        all_ok = False
        print("   FAIL - no remote input. Turn the remote ON and pair it to THIS robot.")

    # Summary
    print("\n" + "-" * 60)
    if all_ok:
        print("ALL GOOD. Next: stand Adam (STAND then WLAK buttons), then:")
        print("   ./run.sh fight-standing")
        print("Or let the script stand him:  ./run.sh fight")
    else:
        print("Some checks FAILED above. Fix those, then run  ./run.sh check  again.")
    print("-" * 60)


def _test_remote(robot: BoosterLowLevelController) -> None:
    """Print remote-controller input so you can confirm it's connected. No motion."""
    from booster_robotics_sdk_python import B1RemoteControllerStateSubscriber

    buttons = ("x", "y", "a", "b", "lb", "rb", "lt", "rt", "ls", "rs",
               "start", "back", "hat_u", "hat_d", "hat_l", "hat_r")

    def on_rc(rc):
        pressed = [name for name in buttons if getattr(rc, name, False)]
        sticks = f"lx={rc.lx:+.2f} ly={rc.ly:+.2f} rx={rc.rx:+.2f} ry={rc.ry:+.2f}"
        if pressed or rc.event:
            print(f"event={hex(rc.event)}  buttons={pressed or '-'}  {sticks}")

    print("\nTEST REMOTE - press buttons / move sticks on the Booster remote.")
    print("You should see lines appear below. Nothing on the robot moves.")
    print("If NOTHING appears when you press buttons, the remote is not connected.")
    print("Ctrl-C to stop.\n")

    sub = B1RemoteControllerStateSubscriber(on_rc)
    sub.InitChannel()
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        stop.wait()
    finally:
        try:
            sub.CloseChannel()
        except Exception:
            pass
        print("\nDone testing remote.")


def _verify_joints(robot: BoosterLowLevelController) -> None:
    """Print live q values so you can confirm which serial indices are the arms.

    Move each arm by hand (robot in DAMP) and watch which indices change.
    """
    print("\nVERIFY JOINTS - move each arm by hand and watch the values change.")
    print(f"Arm order: {ARM_JOINT_NAMES}")
    print(f"DEFAULT indices  {DEFAULT_INDICES}")
    print(f"MOTION_CAPTURE   {USE_MOTION_CAPTURE_INDICES}")
    print("Ctrl-C to stop.\n")
    try:
        while True:
            print("DEFAULT       :", robot.read_low_state_q(list(DEFAULT_INDICES)))
            print("MOTION_CAPTURE:", robot.read_low_state_q(list(USE_MOTION_CAPTURE_INDICES)))
            print("-" * 60)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nDone verifying.")


def _run_remote_trigger(robot: BoosterLowLevelController, args) -> None:
    """Idle loop: START+BACK on the remote toggles boxing on/off. No SSH needed."""
    from booster_robotics_sdk_python import B1RemoteControllerStateSubscriber

    controller = RemoteTriggeredController(robot, speed=args.speed, time_gap_s=0.05)
    sub = B1RemoteControllerStateSubscriber(controller.on_remote)
    sub.InitChannel()

    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    logger.info("Remote-trigger mode ready. Robot is NORMAL until you toggle.")
    logger.info("Stand him up (LT+START, then RT+A), then press START+BACK to start boxing.")
    logger.info("Press START+BACK again to stop boxing. Ctrl-C to exit.")
    try:
        stop.wait()
    finally:
        try:
            sub.CloseChannel()
        except Exception:
            pass
        controller.shutdown()
        robot.set_ready()
        logger.info("Exited remote-trigger mode.")


def main() -> None:
    parser = argparse.ArgumentParser(description="K1 remote-controlled boxing")
    parser.add_argument("--speed", choices=("slow", "medium", "fast"), default="slow")
    parser.add_argument("--network-interface", default="127.0.0.1")
    parser.add_argument(
        "--verify-joints", action="store_true",
        help="Read-only: print arm joint values to confirm indexing (no motion).",
    )
    parser.add_argument(
        "--test-remote", action="store_true",
        help="Read-only: print remote-controller input to confirm it's connected.",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Read-only: one-shot health check (data link, mode, remote).",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the interactive safety confirmation."
    )
    parser.add_argument(
        "--already-standing", action="store_true",
        help="Robot is already standing/balancing (you used the STAND+WALK buttons "
             "or app). Skips the auto stand-up; only enables arm control.",
    )
    parser.add_argument(
        "--damp-on-exit", action="store_true",
        help="On exit, go limp (DAMP) instead of staying upright in ready mode. "
             "Only use this if the robot is supported/hanging.",
    )
    parser.add_argument(
        "--wait-standing", action="store_true",
        help="Wait until the robot is stood up (WALK mode) before activating boxing.",
    )
    parser.add_argument(
        "--auto", action="store_true",
        help="Hands-free demo: wait until the robot is stood up, then activate boxing "
             "(implies --yes --already-standing --wait-standing). For the autostart service.",
    )
    parser.add_argument(
        "--remote-trigger", action="store_true",
        help="Idle until you press START+BACK on the remote to toggle boxing on/off. "
             "No SSH needed each time; robot stays normal until you toggle. (implies --yes)",
    )
    args = parser.parse_args()

    if args.auto:
        args.yes = True
        args.already_standing = True
        args.wait_standing = True
    if args.remote_trigger:
        args.yes = True

    robot = BoosterLowLevelController(network_interface=args.network_interface)

    try:
        robot.init(network_interface=args.network_interface)
    except ImportError:
        logger.error("Booster SDK not installed. Build it from development/legacy/sdk.")
        return
    except Exception as exc:
        logger.error("Failed to init robot: %s", exc)
        return

    if args.check:
        _doctor(robot)
        robot.close()
        return

    if args.test_remote:
        _test_remote(robot)
        robot.close()
        return

    if args.verify_joints:
        _verify_joints(robot)
        robot.close()
        return

    if not _confirm(args.yes):
        logger.info("Aborted by user.")
        robot.close()
        return

    if args.remote_trigger:
        _run_remote_trigger(robot, args)
        robot.close()
        return

    logger.info("Starting fight mode at %s speed.", args.speed)

    from booster_robotics_sdk_python import B1RemoteControllerStateSubscriber

    sm = None
    sub = None
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    try:
        # Hands-free: wait until a human stands the robot up (STAND then WLAK).
        if args.wait_standing:
            logger.info("Waiting for the robot to be stood up (press STAND then WLAK)...")
            while not stop.is_set():
                if robot.is_walking():
                    logger.info("Robot is balancing (WALK) - activating boxing.")
                    break
                stop.wait(1.0)
            if stop.is_set():
                return  # cleanup happens in finally

        # NOTE: if not already standing, this stands the robot up
        # (DAMP -> kPrepare -> kWalking), then takes the guard pose. Be ready.
        sm = FightingStateMachine(
            robot, speed=args.speed, time_gap_s=0.05,
            already_standing=args.already_standing,
        )

        sub = B1RemoteControllerStateSubscriber(sm.on_remote)
        sub.InitChannel()

        logger.info("Ready. Y=right punch  X=left punch  B=uppercut  A=block  D-pad up=victory")
        logger.info("Ctrl-C to stop.")
        stop.wait()
    finally:
        logger.info("Stopping - returning to guard...")
        # Stop remote input FIRST so no new punch fires during shutdown.
        if sub is not None:
            try:
                sub.CloseChannel()
            except Exception:
                pass
        if sm is not None:
            sm.return_to_guard()
        # Default: stay upright in ready mode (not limp). Opt in to damp if supported.
        if args.damp_on_exit:
            robot.damp()
            logger.info("Stopped. Robot is DAMPED (limp) - make sure it's supported.")
        else:
            robot.set_ready()
            logger.info("Stopped. Robot is in READY mode (still standing).")
        robot.close()


if __name__ == "__main__":
    main()
