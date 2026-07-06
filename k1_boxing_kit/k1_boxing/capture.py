"""Record K1 arm poses by hand (backup if the T1 poses don't fit the K1).

The robot stays in DAMP (limp) the whole time - this only READS joint angles, it
never drives motors. Move the arms by hand, snapshot each keyframe, and it prints
a paste-ready block for k1_boxing/actions.py.

    python3 -m k1_boxing.capture --name LEFT_PUNCH

Then copy the printed block into k1_boxing/actions.py (replacing the matching
sequence), and re-run `./run.sh fight`.
"""

import argparse
import logging

from .lib import BoosterLowLevelController
from .joints import K1_ARM_JOINT_INDICES, ARM_JOINT_NAMES

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("k1_boxing")


def _format_block(name: str, frames) -> str:
    lines = [f"{name} = ["]
    for frame in frames:
        nums = ", ".join(f"{v:.4f}" for v in frame)
        lines.append(f"    ({nums}),")
    lines.append("]")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture K1 arm poses by hand (read-only)")
    parser.add_argument("--name", default="MY_POSE", help="Name for the printed sequence")
    parser.add_argument("--network-interface", default="127.0.0.1")
    args = parser.parse_args()

    robot = BoosterLowLevelController(network_interface=args.network_interface)
    try:
        robot.init(network_interface=args.network_interface)
    except ImportError:
        logger.error("Booster SDK not installed on this machine.")
        return
    except Exception as exc:
        logger.error("Failed to connect: %s", exc)
        return

    print("\n" + "=" * 60)
    print(f"CAPTURE: {args.name}   (robot should be in DAMP - arms move freely)")
    print("=" * 60)
    print(f"Joint order: {ARM_JOINT_NAMES}")
    print("Move the arms by hand, then:")
    print("  ENTER = snapshot this pose")
    print("  undo  = remove last snapshot")
    print("  done  = finish and print the sequence")
    print("-" * 60)

    frames = []
    try:
        while True:
            cmd = input(f"[{len(frames)} frames] ENTER / undo / done: ").strip().lower()
            if cmd == "done":
                break
            if cmd == "undo":
                if frames:
                    frames.pop()
                    print(f"  removed - {len(frames)} left")
                continue
            try:
                values = robot.read_low_state_values(list(K1_ARM_JOINT_INDICES))
            except Exception as exc:
                print(f"  read failed: {exc}")
                continue
            frames.append(values)
            print("  captured: (" + ", ".join(f"{v:.4f}" for v in values) + ")")
    except (EOFError, KeyboardInterrupt):
        print("\nInterrupted.")

    robot.close()

    if not frames:
        print("\nNo frames captured.")
        return

    print("\n" + "=" * 60)
    print("Paste this into k1_boxing/actions.py (before the `_as_dicts` section):")
    print("=" * 60)
    print(_format_block(args.name, frames))
    print("=" * 60)


if __name__ == "__main__":
    main()
