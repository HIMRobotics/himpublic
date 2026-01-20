cmake_minimum_required(VERSION 3.15...3.27)
cmake_policy(SET CMP0048 NEW)

project(
  ${SKBUILD_PROJECT_NAME}
  VERSION ${SKBUILD_PROJECT_VERSION}
  LANGUAGES CXX
)

option(BUILD_PYTHON_BINDING "Build Python Binding" OFF)

set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Global link libs for your examples (as in your original)
link_libraries(booster_robotics_sdk.a fastrtps fastcdr libfoonathan_memory-0.7.3.a)

# ---- Executables (unchanged) ----
add_executable(b1_loco_example_client          example/high_level/b1_loco_example_client.cpp)
add_executable(b1_arm_sdk_example_client       example/high_level/b1_arm_sdk_example.cpp)
add_executable(b1_7dof_arm_sdk_example_client  example/high_level/b1_7dof_arm_sdk_example.cpp)
add_executable(b1_low_level_publisher          example/low_level/low_level_publisher.cpp)
add_executable(b1_low_level_subscriber         example/low_level/low_level_subscriber.cpp)
add_executable(low_level_hand_data_subscriber  example/low_level/low_level_hand_data_subscriber.cpp)
add_executable(b1_low_sdk_example              example/low_level/b1_low_sdk_example.cpp)
add_executable(b1_7dof_arm_low_sdk_example     example/low_level/b1_7dof_arm_low_sdk_example.cpp)
add_executable(odometer_example                example/low_level/odometer_example.cpp)

# FIX: use ${...}, not $(...)
include_directories(BEFORE ${PROJECT_SOURCE_DIR}/include)

# ---- Python binding ----
if(BUILD_PYTHON_BINDING)
  # Prefer a venv if present, otherwise system Python
  set(Python3_FIND_VIRTUALENV FIRST)
  find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
  message(STATUS "Python3 executable: ${Python3_EXECUTABLE}")

  # Install location for binary extensions (.so) should be platlib
  execute_process(
    COMMAND ${Python3_EXECUTABLE} -c "import sysconfig; print(sysconfig.get_paths()['platlib'])"
    OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  include_directories(${Python3_INCLUDE_DIRS})

  # ---- Auto-discover pybind11's CMake package dir from this Python ----
  # Works when 'pip install pybind11' was done into this interpreter's environment
  execute_process(
    COMMAND ${Python3_EXECUTABLE} -c
            "import pathlib, pybind11; print((pathlib.Path(pybind11.__file__).parent/'share'/'cmake'/'pybind11').as_posix())"
    RESULT_VARIABLE _PY_OK
    OUTPUT_VARIABLE _PYBIND11_CMAKE_DIR
    OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET
  )
  if(_PY_OK EQUAL 0 AND EXISTS "${_PYBIND11_CMAKE_DIR}/pybind11Config.cmake")
    set(pybind11_DIR "${_PYBIND11_CMAKE_DIR}" CACHE PATH "pybind11 CMake package dir")
    message(STATUS "Using pybind11 from: ${pybind11_DIR}")
  endif()

  find_package(pybind11 CONFIG REQUIRED)  # defines pybind11::headers, pybind11::module

  # Build the extension with Python helper
  python3_add_library(booster_robotics_sdk_python MODULE
    ${PROJECT_SOURCE_DIR}/python/binding.cpp
    WITH_SOABI
  )

  # Ensure pybind11 include/interface flags are applied
  target_link_libraries(booster_robotics_sdk_python PRIVATE pybind11::headers pybind11::module)
  target_compile_definitions(booster_robotics_sdk_python PRIVATE VERSION_INFO=${PROJECT_VERSION})

  # Optional: generate .pyi stubs (only if tool is present)
  find_program(PYBIND11_STUBGEN_EXECUTABLE pybind11-stubgen)
  if(PYBIND11_STUBGEN_EXECUTABLE)
    add_custom_command(
      TARGET booster_robotics_sdk_python
      POST_BUILD
      COMMAND
        ${CMAKE_COMMAND} -E env
          "PYTHONPATH=$<TARGET_FILE_DIR:booster_robotics_sdk_python>:$ENV{PYTHONPATH}"
          ${Python3_EXECUTABLE} -m pybind11_stubgen
            -o ${CMAKE_SOURCE_DIR}/build
            booster_robotics_sdk_python
      VERBATIM
    )
    install(FILES ${CMAKE_SOURCE_DIR}/build/booster_robotics_sdk_python.pyi
            DESTINATION ${PYTHON_SITE_PACKAGES})
  else()
    message(WARNING "pybind11-stubgen not found; skipping .pyi generation")
  endif()

  install(TARGETS booster_robotics_sdk_python
          LIBRARY DESTINATION ${PYTHON_SITE_PACKAGES})
endif()