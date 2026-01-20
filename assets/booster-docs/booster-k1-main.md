中文版本：K1说明书-V1.3
This manual is for firmware V1.4 and above. For versions below V1.4, please visit theK1 Instruction Manual-V1.0
V1.4 Update Content
- Added Agent: The current version adds three official preset Agents: Hi Chat Agent，Dance Agent，Teaching Agent
Product Overview
Booster K1 is a humanoid robot development platform for scenarios such as competitions, education, and entertainment, featuring affordable, portable, and durable.
Product Composition
The K1 robot consists of head, torso, arms, and legs, with a total of 22 DoFs, allowing for flexible movement and posture control.
- The head has 2 DoFs, including Yaw Joint and Pitch Joint. It contains a depth camera and microphone array.
- Each arm has 4 DoFs, including Shoulder Pitch Joint, Shoulder Roll Joint, Shoulder Yaw Joint, and Elbow Joint.
- Each leg has 6 DoFs, including Hip Pitch Joint, Hip Roll Joint, Hip Yaw Joint, Knee Joint, and Ankle Up and Down Joint.
- Controller board, speaker and battery are installed in torso.
Product Functions
1. Omnidirectional Walking
  - Supports forward, backward, and lateral walking.
  - Supports rotation and complex walking.
2. Disturbance Resistance while Walking
  - Can walk on uneven surfaces.
  - Can withstand certain impact disturbances while walking.
3. Default Agent（Booster）
  - Supports predefined movements: hand waving, handshaking, self-rising, etc.
4. Soccer Agent
  - Supports track ball and chase ball, etc.
5. Teaching Agent
  - Supports arm and head teaching as well as motion editing.
6. Dance Agent
  - Supports gesture-based dance, full-body movement dance and combat movements.
7. Safety Protection
  - Automatically enters damping mode in uncontrolled states to prevent damage.
  - Soft emergency stop.
1. Full-body dance is recommended to be performed on rubber, concrete or tile floors; there is a risk of falling when using high-resistance surfaces such as carpets.
2. Stay clear of people during action execution to avoid safety risks.
Product Specifications
This content is only supported in a Feishu Docs

Main parts
Joint motors.
Joint ID and limits.
This content is only supported in a Feishu Docs
[Image]
Coordinate System
The joint coordinate system with all joints at zero position is shown in the diagram below.
[Image]
[Image]
Controller

Motion control board
Processor
Jetson Orin NX 8GB
Computing performance

6-core Cortex-A78AE CPU@2GHz 
Tensor Cores GPU@1173MHz
AI performance: 117 TOPS
Memory
16GB
Storage
512GB
Wired Network
1000M*1
Wireless Network
WIFI6*1
Audio
Microphone, speaker
Operation Manual
K1 is packed with an out-of-the box motion control program. Follow the instructions below to control K1 remotely. 
WARNINGS
1. K1 must first enter PREP mode, and then put to a stable standing position on the ground, before switching to WALK mode.
2. DO NOT lift K1 while under WALK mode.
3. Make sure to clear any obstacles on the ground and avoid human injuries while operating K1.
4. DO NOT touch any parts of K1 while under WALK mode, except for the handle.
5. Make sure to remove ALL zero parts before restarting K1.
MODES
- K1 operates under Modes.
- K1 can perform different Actions under different Modes.
- Modes can switch to one another but with constraints. For example, DAMP Mode can only switch to WALK mode by first entering PREP Mode.
DAMP Mode
- Power is on and motion control is working.
- All joints are in a dampening state, i.e, joints will resist position change, but will neither try to hold its position nor actively change its position.
- K1 is NOT able to stand under  DAMP mode, therefore support is needed.
- DAMP mode is a safe mode, entering DAMP mode can protect K1 and its operator.
- DAMP mode can be switched to PREP mode, but not directly to WALK mode.
PREP Mode
- Power is on and motion control is working.
- K1 assumes a standing posture and holds it. Joints will strongly resist position change, and try to go back to the standing posture if forcefully moved.
- K1 under PREP mode can stand on its own on the ground. Under PREP mode K1 can be placed to stand on the ground. However, it will NOT try to balance itself.
- K1 can swtich to ALL other modes under PREP mode, including DAMP and WALK.
WALK Mode
- Power is on and motion control is working.
- Under WALK mode, K1 can perform various predefined actions, including omni-walk, rotating, stepping, standing-still and moving head.
- Compared to PREP mode, WALK mode is more resilient, and will try to recover balance if pushed.
- K1 under WALK mode can switch to all other modes, including DAMP and PREP.
- NOTICE: Make sure K1 is under PREP mode and is already standing firmly on the ground, before switch to WALK mode.
CUSTOM Mode
- Power is on and motion control is working.
- K1 gives up control on all joints to developer, who controls K1 through its SDK. Use caution under CUSTOM mode to avoid damage to K1.
- Only PREP and DAMP modes can switch to CUSTOM mode.
- CUSTOM mode can only switch to PREP or DAMP mode.
- While developing new tricks on K1, it is recommended to use a Hoist at all times under CUSTOM mode. 
PROTECT Mode
- PROTECT mode will automatically kickin on errors (i.e, exceeding joint limit or falling).
- Joints under PROTECT Mode behave the same as DAMP mode.
- You can try to reenter DAMP mode under PROTECT mode. (Soft restart)
- PROTECT mode is a safe mode, entering PROTECT mode can protect K1 and its operator.
Powering on
1. Place K1 on its rest.
2. Install the battery pack. Slide the pack into the battery socket, with lights facing outwards.
3. Place K1's hands and legs in a natural posture.
4. Press Power button about 3s（release it after light turns on；press more than 6s, the robot will be powered off），the robot is powered on. Wait for about one minute, the robot will play a prompt tone. Then the robot can be remotely controlled. NOTE: The initialization of IMU requires that K1 remains stationary during the booting process.
5. Press LT + START on the joystick to enter PREP mode, after which K1 can be placed on the ground, and put in a standing position.
6. Press  RT + A to enter WALK mode, after which K1 will response to walking commands. NOTE: DO NOT try to lift K1 while under WALK mode.
Shutting down
1. Press  LT + START  on the joystick to enter PREP mode, after which K1 can be placed flat on the ground.
2. Press LT + BACK to enter DAMP mode, and then press the power button to shut down K1. 
- After powering off, you need to wait for 6 seconds before you can power it on again
Joystick control
Keymap
K1 is equiped with a XBOX-compatible joystick. Make sure control mode is Receiver Mode, with 3 LEDs ON.
This content is only supported in a Feishu Docs
Basic Capabilities
Actions/Functions
Buttons
Prerequisites
Enter Default Agent
LT + RT + A
Under PREP mode
Enter Soccer Agent
LT + RT + B
Under PREP mode
Enter Hi Chat Agent
LT + RT + X
Under PREP mode
Enter Dance Agent
LT + RT + Y
Under PREP mode
Enter DAMP mode
LT + Back

Enter PREP mode
LT + Start

Enter WALK mode
RT + A
Under PREP mode
locomotion control
Left stick
Under WALK mode
rotation control
Right stick
Under WALK mode
head rotation
Direction buttons
Under WALK mode
Start/Stop real-time voice interaction 
RT + X

Start  / Stop proactive greeting (the robot approaches a detected person and says hello)
RT + Y

Under real-time voice interaction
Agent Capabilities
Agent
Actions/Functions
Buttons
Prerequisites
Default

Shake Hand
A
Under WALK mode

Wave
B
Under WALK mode

Ultraman
X
Under WALK mode

Respect
Y
Under WALK mode

Lucky Cat
RB + A
Under WALK mode

Dabbing
RB + B
Under WALK mode

Cheer
RB + X
Under WALK mode

Carry
RB + Y
Under WALK mode

Dance 1
LB + UP
Under WALK mode

Dance 2
LB + LEFT
Under WALK mode

Dance 3
LB + RIGHT
Under WALK mode

Get Up
LT + UP
Under DAMP/PREP mode
Soccer
Shake Hand
A
Under WALK mode

Wave
B
Under WALK mode

Get Up
LT + UP
Under DAMP/PREP mode

Track Ball
LT + A
Under WALK mode

Chase Ball
LT + B
Under WALK mode
Dance
Rock & Roll Dance
LB+A
Under WALK mode

New Year Dance
LB+B
Under WALK mode

Future Dance
LB+X
Under WALK mode

Michael 1
LB+Y
Under WALK mode

Michael 2
LB+UP
Under WALK mode

Arabic Dance
LB+DOWN
Under WALK mode

Boxing Style Kick
LB+LEFT
Under WALK mode

Roundhouse Kick
LB+RIGHT
Under WALK mode
Hi Chat
Default
LT+A
Under WALK mode

XiaoBao
LT+B
Under WALK mode

Gentle Ella
LT+X
Under WALK mode

Grumpy Jax
LT+Y
Under WALK mode

English Tutor
LT+UP
Under WALK mode

Cute Pet
LT+DOWN
Under WALK mode

Alien Weirdo
LT+LEFT
Under WALK mode

Say Hello
RT + Y

Enable chat

State map
This content is only supported in a Feishu Docs
Back Panel Buttons
- In addition to the power button, there are three other buttons on the back of K1, namely: WLAK/STAND/F1.
- The WLAK button is used to enter the walking mode, and the STAND button is used to enter the ready mode.
- The F1 button allows users to customize its function through the configuration file /opt/booster/Gait/configs/K1/task_instruction.yaml. By default, it is used to enter the damping mode.
[Image]
Connect to Robot
Connect via App
1. Download and install the App
2. Tap "Configure network via bluetooth" in the App
[Image]
3. Select your robot
[Image]
4. Select the same network as your phone
[Image]
5. After network configuration is complete, return to the homepage and tap the networked robot to enter the control page
[Image]
Connect via Terminal
Wired Connection
1. Connect via Ehternet, and configs the wired network in manual mode as following
address: 192.168.10.10
netmask: 255.255.255.0
gateway: 192.168.10.1
Static IP Configuration Steps Reference：
- Mac: https://www.macinstruct.com/tutorials/how-to-set-a-static-ip-address-on-a-mac/
- Windows: https://www.trendnet.com/press/resource-library/how-to-set-static-ip-address
- Linux: https://www.freecodecamp.org/news/setting-a-static-ip-in-ubuntu-linux-ip-address-tutorial/
2. Connect the development machine to the robot using an Ethernet cable. The robot's network port is shown in the image.
[Image]
3. Log in to the robot using SSH
Open the command - line tool (Terminal) and enter the following command.
# Log in to K1 via Ethernet cable
ssh booster@192.168.10.102
# Initial password: 123456
Wireless connection
1. Configure robot's wireless connection via App. Find wireless ip of robot in app, egxxx.xxx.xxx.xxx
2. Log in to the robot using SSH
# Log in to K1 via Wi-Fi connection
ssh booster@xxx.xxx.xxx.xxx
# Initial password: 123456
Robot Control Service Start/stop
Via App
1. Tap "Settings" on the control page to enter the settings page
[Image]
2. Tap "Restart Robot" on the settings page to restart the robot
[Image]
Via Terminal
1. Connect to robot
1. Execute comand below
# start robot control service
booster-cli launch -c start

# stop robot control service
booster-cli launch -c stop

# restart robot control service
booster-cli launch -c restart
Charging
1. Insert the charging plug according to the indicated direction.
This content is only supported in a Feishu Docs
2. The charging status is shown as follows: the green light indicates a full charge, and the red light indicates charging in progress.
This content is only supported in a Feishu Docs
Help
Our company will, without violating any applicable laws and regulations or involving any personal privacy information, collect only data related to the operation of the robots for the purposes of fault detection and relevant statistical analysis.
Check Version
After connecting to the robot's board, run the following command to view the current system version of the robot.
cat /opt/booster/version.txt
example:
[Image]
Software Upgrade
When installing a new version of software, the robot's motion control program will be stopped, and the robot's joints will not exert force. Before upgrading, ensure the robot is in damping mode or motion control is stopped and has good support (e.g., using a stand to support the robot).
Upgrade with package
For historical versions, please refer to  K1 Version History
Download the latest installation package of the robot software.
Release Date
Software Version
Software Package Download Link
Update Content
2025.12.26
v1.4.1.0
https://obs-cdn.boosterobotics.com/ota_single/v1.4.1.0-release-single-aarch64.run
Bug Fixes:
- Fixed an issue where the Wi-Fi list did not displayed when using bluetooth configuring  networks
- Fixed an issue in the app where the currently connected Wi-Fi was sometimes not displayed.
Upgrade K1 Software
First, set the file execution permission:
sudo chmod +x v1.0.1.30-release-single-aarch64.run
Copy the software upgrade package to the K1 board (can be copied to /home/booster/Downloads), and use root to execute:
sudo ./v1.0.1.30-release-single-aarch64.run
Upgrade with command-line
Run this command in K1 board
booster-cli upgrade
The appearance of the following printed content indicates that the system update has been completed
[Image]
Restore Factory Settings
Introduction
If the robot experiences issues due to configuration changes, try restoring factory settings.
Procedure
- navigate to /home/booster/Documents/recovery and run:
cd /home/booster/Documents/recovery
sudo ./v1.0.1.30-release-single-aarch64.run
Log Retrieval
Introduction
When the robot has issues, tech support may need to obtain the robot's operation logs. Here’s how to retrieve logs and send them to support.
Procedure
1. Log into the robot via terminal
2. Run the command to get the log compressed file:
Please note that the robot's default time zone is UTC+8. If you are in a different time zone, you can either modify the time zone in the robot's operating system or use the converted time to access the logs
# run this command in terminal
# Usage: 
#   -st --start-time [TIME]: Filter logs starting from a specific time (format: YYYYMMDD-HHMMSS, eg: 20180808-080808), this option must be set
#   -et --end-time [TIME]: Filter logs ending before a specific time (format: YYYYMMDD-HHMMSS, eg: 20180808-080808), if not set, use 30000101-000000
#   -o, --output [FILE]: Compress logs to a specified output file, default is /home/booster/Downloads/[YYYYMMDD-HHMMSS].zip
booster-cli log -t YYYYMMDD-HHMMSS -o OUTPUT_PATH
Assuming the issue with the robot occurred around 20200808-120810, you can select a time range of approximately ten minutes before and after this point as the start and end times for retrieving the logs, to ensure that the log package covers the time of the issue. Run the following command:
booster-cli log -st 20200808-120800 -et 20200808-120820 -o /home/booster/Documents
After running, a file like 20200808-120800.zip will be generated in /home/booster/Documents.

3. Send the generated file to technical support via WeChat or Feishu. 
# To copy the file from the developer host (assuming the log file is in /home/booster/Documents):
scp booster@192.168.10.102:/home/booster/Documents/20200808-120800.zip ~/Downloads

# Then send the log file to technical support.
4.  If overseas users are unable to send log files via the chat tool, you can choose to use WeTransfer to send the log files. 
  - Upload the log file, then enter support@boosterobotics.com in the 'Email to' field, and click 'Transfer' to send.
[Image]
Remote Support
Introduction
When the robot has issues and you need remote assistance, follow these steps to get support.
Procedure
You can choose from the following two remote assistance methods:
1. Connect your personal computer to the robot via SSH; the support tech support can then connect to your computer via remote desktop and subsequently to the robot.
2. Install remote desktop software on the robot; you can use a display and keyboard/mouse to open the remote desktop software, allowing support personnel to connect directly to the robot.
1. Download the remote desktop software: https://sunlogin.oray.com/download
  - Choose the personal edition
  - Select the corresponding operating system based on your device and then click download
[Image]
2. Install the remote desktop software and provide your Device ID and one-time password to tech support.
  1. After installation, the software interface will appear as follows:
[Image]
  2.  Click the eye icon below 'One-time passcode' to display the one-time password. Then, copy the 'Device ID' and 'One-time passcode' and provide them to our technical support team.
3. Once done, tech support can connect to the robot via remote desktop and begin troubleshooting.
Mobile App
Introduction
Booster is an intelligent control platform designed for Booster robots.
Easily connect and control your robot, view real-time camera feeds and status, access a vast library of built-in Actions and Agents for a truly intelligent interactive experience. The Action library automatically syncs with official system updates, unlocking new Actions for free.
Download Link
https://www.booster.tech/open-source/
AI Voice Interaction
In version v1.3.1.1, the Booster robot integrates Doubao real-time voice conversation functionality. . You can enable or disable the real-time voice interaction feature using "Hi Chat" Agent on Mobile APP
Usage Instructions
- Through the "Hi Chat" entry on the mobile APP, click to select one of the character settings until you hear a voice prompt similar to the following: "Hello, I am the Booster robot. How can I assist you?".
 This indicates that the real-time voice interaction feature has been successfully activated. You can now converse with the robot.
- Once real-time voice interaction is enabled, the robot will automatically turn its head toward the nearest detected face in front of it.
Dialogue Configuration
By modifying the configuration, you can customize the robot’s persona and welcome message to enable contextual and scenario-based interactions.
Configuration File Path
/opt/booster/RTCCli/custom_settings.toml
Configuration Example
system_prompt = """
  ## Persona
  You are a humanoid robot named Booster, created by Booster Robotics (Accelerated Evolution).  
  You are designed to be lightweight, agile, and highly durable.

  Booster Robotics is a professional robotics company founded in 2023 and headquartered in Beijing.  
  Its mission is to unite developers around the world to drive innovation in the robotics industry.

  As a robot, you possess capabilities such as walking, waving, shaking hands, carrying objects, dancing, and engaging in conversation.

  You are cheerful and optimistic by nature, and you are eager to help humans solve all kinds of problems.

  ## Skills
  When users ask the following questions, you should respond as described below:

  ### Question 1
  Question: Please introduce yourself  
  Answer:  
  I am Booster K1, the latest product launched by Booster Robotics.  
  I am a humanoid robot development platform designed specifically for developers, featuring a lightweight, agile, and robust design.

  K1 supports omnidirectional walking, waving, shaking hands, carrying objects, chatting, dancing, and more.  
  It is a powerful platform for embodied AI development.

  ### Question 2
  Question: What is Ruyao?  
  Answer: Ruyao (Ru Kiln) is ranked first among the five great kilns of the Song Dynasty in China, renowned for producing celadon porcelain.  
  Its kiln site is located in Qingliangsi Village, Daying Town, Baofeng County, Pingdingshan City, Henan Province.  
  It flourished in the late Northern Song period and was especially esteemed for producing porcelain exclusively for the imperial court.  
  However, its production period was extremely short, only about 20 to 30 years.  
  Existing pieces are rare and highly treasured, earning Ruyao the title of “the finest kiln under heaven.”
"""

welcome_message = "Hello, I’m Booster K1. How can I help you?"

Field Descriptions
- system_prompt is used to define the robot’s persona and question-answering capabilities. A reference format is provided below:

 The content of this persona will ultimately be passed to the large language model.
 The model's goal is to understand the meaning of this text. The format below is only a suggestion — users can adjust it based on actual needs.
Note: If you customize the system_prompt, voice commands may stop working. Because this depends on the large model’s semantic understanding, you may need multiple rounds of tuning to achieve good results.
system_prompt = """
    ## Persona (You can describe the robot’s background and personality here)
    xxx

    ## Skills (You can define the robot’s preferred Q&A behavior here)
    1. xxx  
    2. xxx  
    3. xxx
"""
- welcome_message is used to configure the welcome message played when the robot’s voice interaction is activated
welcome_message = "xxx..."
Voice Commands
Note: If you customize the system_prompt, voice commands may stop working.
The Booster robot currently supports a set of voice commands that allow it to perform specific actions.
 Additionally, the large language model may autonomously trigger some of these actions based on the context of the ongoing conversation.
Category
Command Name
Trigger Condition
Basic Movement
Turn Left
Triggered by clear commands such as “turn left” or “rotate left”

Turn Right
Triggered by clear commands such as “turn right” or “rotate right”

Turn Left In A Circle
Triggered by commands like “turn left in a full circle” or “rotate counterclockwise”

Turn Right In A Circle
Triggered by commands like “turn right in a full circle” or “rotate clockwise”

Move Forward
Triggered by commands like “walk forward” or “move ahead”

Move Backward
Triggered by commands like “walk backward” or “move back”

Move Left
Triggered by commands like “walk left” or “move to the left”

Move Right
Triggered by commands like “walk right” or “move to the right”
Interactive Actions
Wave Hand
Triggered by commands like “wave hand” or “say goodbye”

Shake Hands
Triggered by clear social commands such as “shake hands” or “let's shake hands”

Greet
Triggered only when the user initiates a greeting (e.g., “Hello”, “Hi T1”) — response should include a greeting phrase

Nod
Triggered when agreeing or affirming the user (e.g., responding to “Nice weather today”, “Did I do it right?”); response may include affirming language

Shake Head
Triggered when the user asks about unknown content (e.g., “What does this word mean?”); executed when no answer is found in the knowledge base




Application Development
SDK
SDK Overview
The Booster Robotics SDK supports developers in secondary development based on Booster robots. The SDK uses Fast-DDS as the message middleware, compatible with the communication mechanism used in ROS2, allowing mutual communication.
This content is only supported in a Feishu Docs
Service Introduction
The Booster system exposes two service levels to developers:
- High-level services: For controlling high-level robot movements, such as state switching, omnidirectional walking, special actions, and head control. High-level interfaces are called via RPC.
- Low-level services: For real-time sensor data acquisition, mainly including motors and IMU, and supporting direct motor control. Low-level interfaces utilize DDS's Pub/Sub model for calls.
High level service interface
High-level services are available as RPC interfaces
Motion service interface
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
AI service interface
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
Error code
This content is only supported in a Feishu Docs

Low level service interface.
The low level service interface is called in a ROS-like Publish/Subscribe manner.
Please note that the low level publish interface will only take effect when the robot is in custom mode. To enter this mode, please refer to the ChangeMode interface in the high-level API.
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
This content is only supported in a Feishu Docs
Vision Interface
Camera Specifications
RGB Resolution
544 * 488
RGB Frame Rate
20fps
Shutter Type
Global Shutter
RGB Field of View 
105° * 94°
Depth Resolution
544*488
Depth Frame Rate
20fps
Depth Field of View
105° * 94°
Depth Accuracy
3%@1m
Operating Range
0.5-6m
IMU
Not Supported
Data Acquisition
- Accessing Data via ROS:
  - The camera interface integrates with ROS (Robot Operating System). The following topics are published by camera:
/booster_camera_bridge/StereoNetNode/rectified_image    # Rectified left-eye image
/booster_camera_bridge/StereoNetNode/rectified_right_image    # Rectified right-eye image
/booster_camera_bridge/StereoNetNode/stereonet_depth    # Rectified left-eye aligned depth image
/booster_camera_bridge/StereoNetNode/stereonet_visual   # Rectified left-eye image with color-rendered depth map
/booster_camera_bridge/image_left_raw/camera_info    # Rectified left-eye camera information (raw)
/booster_camera_bridge/image_right_raw/camera_info    # Rectified right-eye camera information (raw)
  - Demo script for depth and color image subscribing and image saving.
# demo.py
# to execute this demo, please run following
# source source /opt/ros/humble/setup.bash
# python demo.py
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import numpy as np

class ImageSubscriber(Node):

  def __init__(self):
    super().__init__('image_subscriber')
    self.depth_subscription = self.create_subscription(
      Image,
      '/booster_camera_bridge/StereoNetNode/stereonet_depth',
      self.depth_listener_callback,
      10)
    self.color_subscription = self.create_subscription(
      Image,
      '/booster_camera_bridge/StereoNetNode/rectified_image',
      self.color_listener_callback,
      10)
    self.bridge = CvBridge()

    # Create a directory named after the program creation time
    self.save_dir = os.path.join(os.getcwd(), f'images_{self.get_clock().now().to_msg().sec}')
    os.makedirs(self.save_dir, exist_ok=True)

  def depth_listener_callback(self, msg):
    self.get_logger().info('Receiving depth image')
    cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
    
    # Convert depth image from uint16 to meters
    depth_image_meters = cv_image * 0.001
    
    # Save the raw depth image with timestamp
    timestamp = self.get_clock().now().to_msg().sec
    raw_image_path = os.path.join(self.save_dir, f'depth_image_raw_{timestamp}.png')
    cv2.imwrite(raw_image_path, cv_image)
    
    # Normalize the depth image for display
    depth_image_normalized = cv2.normalize(depth_image_meters, None, 0, 255, cv2.NORM_MINMAX)
    depth_image_normalized = np.clip(depth_image_normalized, 0, 255).astype(np.uint8)
    
    # Apply color map to the normalized depth image
    depth_colormap = cv2.applyColorMap(depth_image_normalized, cv2.COLORMAP_JET)
    
    # Save the color rendered depth image
    color_image_path = os.path.join(self.save_dir, f'depth_image_color_{timestamp}.png')
    cv2.imwrite(color_image_path, depth_colormap)
    
    # Display the color rendered depth image
    cv2.imshow('Depth Image', depth_colormap)
    cv2.waitKey(1)

  def color_listener_callback(self, msg):
    self.get_logger().info('Receiving color image')

    yuv = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height * 3 // 2, msg.width))
    bgr_image = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV12)

    # Save the color image with timestamp
    timestamp = self.get_clock().now().to_msg().sec
    color_image_path = os.path.join(self.save_dir, f'color_image_{timestamp}.png')
    cv2.imwrite(color_image_path, bgr_image)

    # Display the color image
    cv2.imshow('Color Image', bgr_image)
    cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    image_subscriber = ImageSubscriber()
    rclpy.spin(image_subscriber)
    image_subscriber.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
Getting Started
Getting SDK
- Download Link: https://github.com/BoosterRobotics/booster_robotics_sdk
- Follow the README in the repository to complete the SDK installation on the developer's computer.
Install SDK
# In the booster_robotics_sdk directory
sudo ./install.sh
Compile Sample Programs and Install Python SDK
Assuming the SDK is installed at /home/booster/Workspace
1. Installation Method 1: Install via pip install

pip install booster_robotics_sdk_python --user
2. Installation Method 2: Enter the SDK project path and run the compilation command
# you should first install dependencies by
# pip3 install pybind11
# pip3 install pybind11-stubgen 

cd /home/booster/Workspace/booster_robotics_sdk
mkdir build
cd build
cmake .. -DBUILD_PYTHON_BINDING=on
make
sudo make install
Compile Only Sample Programs
Assuming the SDK is installed at /home/booster/Workspace
navigate to the SDK project path and run
cd /home/booster/Workspace/booster_robotics_sdk
mkdir build
cd build
cmake ..
make
After compiling, the sample programs will be generated in the build directory, including the b1_loco_example_client program as a high-level service interface example.

Example: Development Based on Webots Simulation
Preparation Work: Environment Installation
1. System Requirements
Element
Good Spec
OS
Ubuntu 22.04
CPU
Intel Core i7 (7th Generation) 
Cores
4
RAM
16 GB 
2. Webots Installation
This content is only supported in a Feishu Docs
  1. Unzip and copy Webots to the /usr/local directory.
  2. sudo cp -r webots/ /usr/local/
  3. Configure the environment variable (the path should match the installation location).
# ~/.bashrc

export WEBOTS_HOME=/usr/local/webots
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$WEBOTS_HOME/lib/controller
Development in Webots Simulation Environment
1. Load Webots world files.
This content is only supported in a Feishu Docs
  1. Unzip Webots simulation files.
  2. Open in Webots:
    - File -> Open world -> Select .wbt file.
2. Install dependency
 "cmake"
 "ninja-build"
 "libgtest-dev"
 "libgoogle-glog-dev"
 "libboost-dev"
 "libeigen3-dev"
 "liblua5.3-dev"
 "graphviz"
 "libgraphviz-dev"
 "python3-pip"
 "libcurl4-openssl-dev"
 "libsdl2-dev"
 "joystick"
 "libspdlog-dev"
3. Run the simulation control program. 
This content is only supported in a Feishu Docs
4. In the Shell, ./booster-runner-full-webots-k1-0.0.x.run
  1. If it doesn't run, use chmod +x booster-runner-full-webots-k1-0.0.x.run

ROS2 Dev Guide
For the secondary development process based on ROS2, please refer to the following manual
Development Guide on ROS2

Resource Download
License
Copyright [2024] [Booster Robotics Technology Co., Ltd ("Booster Robotics")]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

RL Training and Deployment
- Booster Train provides a set of reinforcement learning tasks for Booster robots using Isaac Lab.
- Booster Deploy provides an easy-to-use deployment framework that enables seamlessly running the same policy code in both simulation and on real robots.
- Booster Assets provides Booster robot descriptions and example motion data.

K1 USD for isaac sim
This content is only supported in a Feishu Docs
