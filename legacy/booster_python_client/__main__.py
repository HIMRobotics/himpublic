import argparse
import logging
import signal
import threading

from booster_robotics_sdk_python import B1RemoteControllerStateSubscriber, RobotMode

from .helpers import play_sound

from .state_machine import FightingStateMachine, CameraStateMachine
from .lib import BoosterLowLevelController

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booster_python_client")
# set pygatt log level to WARNING to reduce noise
logging.getLogger("pygatt").setLevel(logging.WARNING)

EVENT_AXIS, EVENT_HAT, EVENT_BTN_DN, EVENT_BTN_UP, EVENT_REMOVE = (
    0x600,
    0x602,
    0x603,
    0x604,
    0x606,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fight Mode FSM Controller")
    parser.add_argument(
        "--speed",
        type=str,
        default="medium",
        help="Motion speed setting (slow, medium, fast)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="fight",
        help="Robot mode (fight, camera)",
    )
    parser.add_argument(
        "--network-interface",
        type=str,
        default="127.0.0.1",
        help="Network interface to use 127.0.0.1 or <interface>",
    )

    args = parser.parse_args()
    logger.info(f"Using speed setting: {args.speed}")
    if args.speed not in ("slow", "medium", "fast"):
        raise ValueError("Invalid speed setting. Must be 'slow', 'medium', or 'fast'")
    if args.mode not in ("fight", "camera"):
        raise ValueError("Invalid mode setting. Must be 'fight' or 'camera'")
    try:

        robot = BoosterLowLevelController()
        robot.init(network_interface=args.network_interface)

        if args.mode == "fight":
            logger.info("Using fight mode")
            play_sound("opening-bell.wav")
            sm = FightingStateMachine(robot, speed=args.speed, time_gap_s=0.05)
        else:
            from .fingerbot import connect_to_kyles_fingerbot

            logger.info("Using camera mode")
            try:
                fingerbot = connect_to_kyles_fingerbot()
                sm = CameraStateMachine(robot, fingerbot, speed="slow", time_gap_s=0.05)
            except Exception as e:
                logger.warning(f"Failed to connect to fingerbot: {e}")

        sub = B1RemoteControllerStateSubscriber(sm.on_remote)
        sub.InitChannel()

        # --- clean, signal-friendly blocker ---
        stop = threading.Event()

        def _handle_stop(signum, frame):
            stop.set()

        # Handle Ctrl-C and kill
        signal.signal(signal.SIGINT, _handle_stop)
        signal.signal(signal.SIGTERM, _handle_stop)

        # Block here until a stop signal arrives
        stop.wait()  # no busy loop, no CPU burn
    finally:
        # Always clean up no matter how we exit
        try:
            if args.mode == "camera":
                fingerbot.disconnect()
            sub.close()
        except Exception as e:
            logger.error("Close error:", e)
        logger.info("Stopping")
