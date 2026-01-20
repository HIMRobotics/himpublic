from pathlib import Path
from typing import Dict, List, Tuple

from booster_robotics_sdk_python import (
    MotorCmd,
    B1JointIndex,
    MotorState,
)


def tuple_to_joint_dict(
    joint_indices: List[B1JointIndex], values: Tuple[float, ...]
) -> Dict[B1JointIndex, float]:
    if len(joint_indices) != len(values):
        raise ValueError("Length of joint_indices and values must match")
    return {joint_indices[i]: values[i] for i in range(len(joint_indices))}


def stringify_motor_cmds(cmds: List[MotorCmd]) -> str:
    s = ""
    for i, cmd in enumerate(cmds):
        s += f"  Motor {i}: mode={cmd.mode}, q={cmd.q:.2f}, dq={cmd.dq:.2f}, tau={cmd.tau:.2f}, kp={cmd.kp:.1f}, kd={cmd.kd:.1f}, weight={cmd.weight:.1f}\n"
    return s


def stringify_motor_states(states: List[MotorState], start: int, stop: int) -> str:
    s = ""
    for i, state in enumerate(states):
        if i < start or i >= stop:
            continue
        s += f"  Motor {i}: q={state.q:.2f}, dq={state.dq:.2f}, mode={state.mode:.2f}, temperature={state.temperature:.1f}\n"
    return s


def stringify_q_values(states: List[MotorState], indices: List[int]) -> str:
    q_values = []
    for i in indices:
        q_values.append(states[i].q)
    return "(" + ", ".join([f"{q:.4f}" for q in q_values]) + ")"


def fire_and_forget(callable, *args, **kwargs):
    """Run a callable in the background, ignoring any exceptions."""
    import threading
    import logging

    def wrapper():
        try:
            callable(*args, **kwargs)
        except Exception as e:
            logging.error(f"Error in fire_and_forget: {e}")

    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()


def play_sound(sounds_file: str):
    """Play a sound file using the system's default player."""
    import subprocess

    curr_dir = Path(__file__).parent
    file_path = curr_dir / "sounds" / sounds_file
    subprocess.run(["aplay", file_path.absolute()])
