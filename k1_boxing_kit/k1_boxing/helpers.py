"""Small pure helpers and shared types for the K1 boxing package."""

from typing import Dict, List, Literal, Sequence, Tuple

SpeedType = Literal["slow", "medium", "fast"]


def tuple_to_joint_dict(
    joint_indices: Sequence[int], values: Tuple[float, ...]
) -> Dict[int, float]:
    """Zip an (index -> angle) mapping, guarding against length mismatch."""
    if len(joint_indices) != len(values):
        raise ValueError(
            f"joint_indices ({len(joint_indices)}) and values ({len(values)}) must match"
        )
    return {joint_indices[i]: values[i] for i in range(len(joint_indices))}


def clamp(value: float, limit: float) -> float:
    """Symmetric clamp used as a last-resort safety guard on commanded angles."""
    return max(-limit, min(limit, value))


def stringify_q_values(states: List, indices: Sequence[int]) -> str:
    """Format selected motor q values for the --verify-joints readout."""
    parts = []
    for i in indices:
        try:
            parts.append(f"[{i}]={states[i].q:.4f}")
        except IndexError:
            parts.append(f"[{i}]=<out-of-range>")
    return "  ".join(parts)
