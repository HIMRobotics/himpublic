from booster_robotics_sdk_python import ChannelFactory, B1LowStateSubscriber
import time


def handler(low_state_msg):
    print("Received message:")
    print(f"  serial motor count: {len(low_state_msg.motor_state_serial)}")
    print(f"  parallel motor count: {len(low_state_msg.motor_state_parallel)}")
    imu_state = low_state_msg.imu_state
    print(f"  imu: {imu_state.rpy[0]}, {imu_state.rpy[1]}, {imu_state.rpy[2]}, "
          f"{imu_state.gyro[0]}, {imu_state.gyro[1]}, {imu_state.gyro[2]}, "
          f"{imu_state.acc[0]}, {imu_state.acc[1]}, {imu_state.acc[2]}")
    for i, motor in enumerate(low_state_msg.motor_state_serial):
        print(f"  serial motor {i}: {motor.dq}, {motor.ddq}, {motor.tau_est}")
    for i, motor in enumerate(low_state_msg.motor_state_parallel):
        print(
            f"  parallel motor {i}: {motor.dq}, {motor.ddq}, {motor.tau_est}")
    print("done")


def main():
    ChannelFactory.Instance().Init(0)
    channel_subscriber = B1LowStateSubscriber(handler)
    channel_subscriber.InitChannel()
    print("init handler")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
