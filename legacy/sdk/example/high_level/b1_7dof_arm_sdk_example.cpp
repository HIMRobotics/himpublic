#include <array>
#include <chrono>
#include <iostream>
#include <thread>


#include <booster/idl/b1/LowCmd.h>
#include <booster/idl/b1/MotorCmd.h>
#include <booster/robot/channel/channel_publisher.hpp>
#include <booster/robot/b1/b1_api_const.hpp>

static const std::string kTopicArmSDK = "rt/joint_ctrl";

int main(int argc, char const *argv[]) {
  if (argc < 2) {
    std::cout << "Usage: " << argv[0] << " networkInterface" << std::endl;
    exit(-1);
  }

  booster::robot::ChannelFactory::Instance()->Init(0, argv[1]);

  booster::robot::ChannelPublisherPtr< booster_interface::msg::LowCmd>
      arm_sdk_publisher;
  booster_interface::msg::LowCmd msg;

  arm_sdk_publisher.reset(
      new booster::robot::ChannelPublisher<booster_interface::msg::LowCmd>(
          kTopicArmSDK));
  arm_sdk_publisher->InitChannel();

  std::array<booster::robot::b1::JointIndexWith7DofArm, 14> arm_joints = {
      booster::robot::b1::JointIndexWith7DofArm::kLeftShoulderPitch,  booster::robot::b1::JointIndexWith7DofArm::kLeftShoulderRoll,
      booster::robot::b1::JointIndexWith7DofArm::kLeftElbowPitch,    booster::robot::b1::JointIndexWith7DofArm::kLeftElbowYaw,
      booster::robot::b1::JointIndexWith7DofArm::kLeftWristPitch,    booster::robot::b1::JointIndexWith7DofArm::kLeftWristYaw,
      booster::robot::b1::JointIndexWith7DofArm::kLeftHandRoll,
      booster::robot::b1::JointIndexWith7DofArm::kRightShoulderPitch, booster::robot::b1::JointIndexWith7DofArm::kRightShoulderRoll,
      booster::robot::b1::JointIndexWith7DofArm::kRightElbowPitch,   booster::robot::b1::JointIndexWith7DofArm::kRightElbowYaw,
      booster::robot::b1::JointIndexWith7DofArm::kRightWristPitch,   booster::robot::b1::JointIndexWith7DofArm::kRightWristYaw,
      booster::robot::b1::JointIndexWith7DofArm::kRightHandRoll
      };

  // init control params
  float weight = 0.f;
  float weight_rate = 0.2f;

  float kp = 55.f;
  float kd = 1.5f;
  float dq = 0.f;
  float tau_ff = 0.f;

  float control_dt = 0.02f;
  float max_joint_velocity = 0.5f;

  float weight_margin = weight_rate * control_dt;
  float max_joint_delta = max_joint_velocity * control_dt;
  auto sleep_time =
      std::chrono::milliseconds(static_cast<int>(control_dt / 0.001f));

  std::array<float, 14> init_pos{};

  std::array<float, 14> target_pos = {0.25f, -1.4,  0.0, -0.5, 0, 0, 0,
                                     0.25f, 1.4, 0.f, 0.5, 0, 0, 0};

  // wait for init
  std::cout << "Press ENTER to init arms ...";
  std::cin.get();

  // set init pos
  std::cout << "Initailizing arms ...";
  float init_time = 5.0f;
  int init_time_steps = static_cast<int>(init_time / control_dt);

  for (size_t i = 0; i < booster::robot::b1::kJointCnt7DofArm; i++) {
      booster_interface::msg::MotorCmd motor_cmd;
      msg.motor_cmd().push_back(motor_cmd);
  }

  // init joints
  for (int i = 0; i < init_time_steps; ++i) {
    // increase weight
    weight += weight_margin;
    weight = std::clamp(weight, 0.f, 0.5f);
    std::cout << weight << std::endl;

    // set control joints
    for (int j = 0; j < init_pos.size(); ++j) {
      msg.motor_cmd().at(int(arm_joints.at(j))).q(init_pos.at(j));
      msg.motor_cmd().at(int(arm_joints.at(j))).dq(dq);
      msg.motor_cmd().at(int(arm_joints.at(j))).kp(kp);
      msg.motor_cmd().at(int(arm_joints.at(j))).kd(kd);
      msg.motor_cmd().at(int(arm_joints.at(j))).tau(tau_ff);
      msg.motor_cmd().at(int(arm_joints.at(j))).weight(weight);
    }

    // send dds msg
    arm_sdk_publisher->Write(&msg);

    // sleep
    std::this_thread::sleep_for(sleep_time);
  }

  std::cout << "Done!" << std::endl;

  // wait for control
  std::cout << "Press ENTER to start arm ctrl ..." << std::endl;
  std::cin.get();

  // start control
  std::cout << "Start arm ctrl!" << std::endl;
  float period = 10.f;
  int num_time_steps = static_cast<int>(period / control_dt);

  std::array<float, 14> current_jpos_des{};

  // lift arms up
  for (int i = 0; i < num_time_steps; ++i) {
    // update jpos des
    for (int j = 0; j < init_pos.size(); ++j) {
      current_jpos_des.at(j) +=
          std::clamp(target_pos.at(j) - current_jpos_des.at(j),
                     -max_joint_delta, max_joint_delta);
    }

    // set control joints
    for (int j = 0; j < init_pos.size(); ++j) {
      msg.motor_cmd().at(int(arm_joints.at(j))).q(current_jpos_des.at(j));
      msg.motor_cmd().at(int(arm_joints.at(j))).dq(dq);
      msg.motor_cmd().at(int(arm_joints.at(j))).kp(kp);
      msg.motor_cmd().at(int(arm_joints.at(j))).kd(kd);
      msg.motor_cmd().at(int(arm_joints.at(j))).tau(tau_ff);
    }

    // send dds msg
    arm_sdk_publisher->Write(&msg);

    // sleep
    std::this_thread::sleep_for(sleep_time);
  }

  std::cout << "Done!" << std::endl;

  return 0;
}
