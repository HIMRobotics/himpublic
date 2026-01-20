from booster_robotics_sdk_python import ChannelFactory, B1OdometerStateSubscriber
import time


def handler(odometer_msg):
    print("Received message:")
    print(f"  Odometer: {odometer_msg.x}, {odometer_msg.y}, {odometer_msg.theta} ")


def main():
    ChannelFactory.Instance().Init(0)
    channel_subscriber = B1OdometerStateSubscriber(handler)
    channel_subscriber.InitChannel()
    print("init handler")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
