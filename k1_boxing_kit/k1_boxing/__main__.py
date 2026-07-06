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
from .state_machine import FightingStateMachine
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
        "--yes", action="store_true", help="Skip the interactive safety confirmation."
    )
    parser.add_argument(
        "--already-standing", action="store_true",
        help="Robot is already standing/balancing (you used the STAND+WALK buttons "
             "or app). Skips the auto stand-up; only enables arm control.",
    )
    args = parser.parse_args()

    robot = BoosterLowLevelController(network_interface=args.network_interface)

    try:
        robot.init(network_interface=args.network_interface)
    except ImportError:
        logger.error("Booster SDK not installed. Build it from development/legacy/sdk.")
        return
    except Exception as exc:
        logger.error("Failed to init robot: %s", exc)
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

    logger.info("Starting fight mode at %s speed.", args.speed)

    from booster_robotics_sdk_python import B1RemoteControllerStateSubscriber

    sm = None
    sub = None
    stop = threading.Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    signal.signal(signal.SIGTERM, lambda *_: stop.set())

    try:
        # NOTE: this stands the robot up and starts balancing
        # (DAMP -> kPrepare -> kWalking), then takes the guard pose. Be ready.
        sm = FightingStateMachine(
            robot, speed=args.speed, time_gap_s=0.05,
            already_standing=args.already_standing,
        )

        sub = B1RemoteControllerStateSubscriber(sm.on_remote)
        sub.InitChannel()

        logger.info("Ready. RT=right punch  RB=right uppercut  LT=left punch  A=block  B=victory")
        logger.info("Ctrl-C to stop.")
        stop.wait()
    finally:
        logger.info("Stopping - returning to guard and damping.")
        # Stop remote input FIRST so no new punch fires during shutdown.
        if sub is not None:
            try:
                sub.CloseChannel()
            except Exception:
                pass
        if sm is not None:
            sm.return_to_guard()
        robot.damp()  # always leave the robot limp/safe
        robot.close()
        logger.info("Stopped cleanly. Robot is damped.")


if __name__ == "__main__":
    main()
