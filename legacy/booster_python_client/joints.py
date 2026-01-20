from booster_robotics_sdk_python import B1JointIndex

ARM_JOINTS_RIGHT = [
    B1JointIndex.kRightShoulderPitch,  # forward/back
    B1JointIndex.kRightShoulderRoll,  # lateral
    B1JointIndex.kRightElbowPitch,  # extend/flex
    B1JointIndex.kRightElbowYaw,
]

ARM_JOINTS_LEFT = [
    B1JointIndex.kLeftShoulderPitch,  # forward/back
    B1JointIndex.kLeftShoulderRoll,  # lateral
    B1JointIndex.kLeftElbowPitch,  # extend/flex
    B1JointIndex.kLeftElbowYaw,
]

RIGHT_ARM_TORSO_JOINTS_INDICES = [
    int(B1JointIndex.kRightShoulderPitch),  # forward/back
    int(B1JointIndex.kRightShoulderRoll),  # lateral
    int(B1JointIndex.kRightElbowPitch),  # extend/flex
    int(B1JointIndex.kRightElbowYaw),
    int(B1JointIndex.kWaist),  # twist
]

LEFT_ARM_TORSO_JOINTS_INDICES = [
    int(B1JointIndex.kLeftShoulderPitch),  # forward/back
    int(B1JointIndex.kLeftShoulderRoll),  # lateral
    int(B1JointIndex.kLeftElbowPitch),  # extend/flex
    int(B1JointIndex.kLeftElbowYaw),
    int(B1JointIndex.kWaist),  # twist
]

LEFT_RIGHT_ARM_TORSO_JOINTS_INDICES = [
    int(B1JointIndex.kLeftShoulderPitch),  # forward/back
    int(B1JointIndex.kLeftShoulderRoll),  # lateral
    int(B1JointIndex.kLeftElbowPitch),  # extend/flex
    int(B1JointIndex.kLeftElbowYaw),
    int(B1JointIndex.kRightShoulderPitch),  # forward/back
    int(B1JointIndex.kRightShoulderRoll),  # lateral
    int(B1JointIndex.kRightElbowPitch),  # extend/flex
    int(B1JointIndex.kRightElbowYaw),
]
