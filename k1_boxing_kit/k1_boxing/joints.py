"""K1 arm joint indexing.

SAFETY-CRITICAL: these indices decide WHICH physical joints move. Commanding the
wrong index can drive a joint into itself or the body. VERIFY on the real K1 with
`python3 -m k1_boxing --verify-joints` before enabling any motion.

Background:
  - The official K1 joint order (booster_assets K1_JOINT_NAMES) and Kyle's working
    T1 fight code both place the 8 arm joints at serial indices 2..9, with NO waist
    on the K1 (the T1's waist sits at 10, shifting only the legs).
  - HOWEVER, this repo's own himpublic/code/motion_capture.py uses arm indices
    12..19 for the K1. That disagreement is exactly why --verify-joints exists.
  - If verification shows the arms live at 12..19 on your K1, set
    K1_ARM_JOINT_INDICES to USE_MOTION_CAPTURE_INDICES below.
"""

# Canonical order for every punch tuple: they are authored as
# (LeftShoulderPitch, LeftShoulderRoll, LeftElbowPitch, LeftElbowYaw,
#  RightShoulderPitch, RightShoulderRoll, RightElbowPitch, RightElbowYaw)
ARM_JOINT_NAMES = (
    "left_shoulder_pitch",
    "left_shoulder_roll",
    "left_elbow_pitch",
    "left_elbow_yaw",
    "right_shoulder_pitch",
    "right_shoulder_roll",
    "right_elbow_pitch",
    "right_elbow_yaw",
)

# Default: matches B1JointIndex / official K1_JOINT_NAMES (arms before the (absent) waist).
DEFAULT_INDICES = (2, 3, 4, 5, 6, 7, 8, 9)

# Alternative used by himpublic/code/motion_capture.py. Switch to this ONLY if
# --verify-joints shows the arms respond at these indices on your K1.
USE_MOTION_CAPTURE_INDICES = (12, 13, 14, 15, 16, 17, 18, 19)

# The active mapping. Change this one line if verification requires it.
K1_ARM_JOINT_INDICES = DEFAULT_INDICES
