# Booster Robotics SDK
Booster Robotics SDK aims to provide a simple and easy-to-use interface for developers to control the Booster Robotics products. 

## Prebuild environment
* OS  (Ubuntu 22.04 LTS)  
* CPU  (aarch64 and x86_64)   
* Compiler  (gcc version 11.4.0) 

## Installation
```bash
sudo ./install.sh
```

## Install python package for building python binding locally
```bash
pip3 install pybind11
pip3 install pybind11-stubgen
```

## Build examples
```bash
mkdir build
cd build
cmake ..
make
```

## Run examples
### 1. run b1_arm_sdk_example_client locally
```
cd build
./b1_arm_sdk_example_client 127.0.0.1
```
### 2. run b1_7dof_arm_sdk_example_client locally
```
cd build
./b1_7dof_arm_sdk_example_client 127.0.0.1
```
### 3. run other example xxx locally
```
cd build
./xxx 127.0.0.1
```

## Build python binding api and install
```bash
mkdir build
cd build
cmake .. -DBUILD_PYTHON_BINDING=on
make
sudo make install
```

if pybind11-stubgen cannot be found even after pip install, export PATH
```bash
export PATH=/home/[user name]/.local/bin:$PATH
```

## License

This project is licensed under the Apache License, Version 2.0. See the LICENSE file for details.

This project uses the following third-party libraries:
- fastDDS (Apache License 2.0)
- pybind11 (BSD 3-Clause License)
- pybind11-stubgen (MIT License)