#!/usr/bin/env bash
#
# Booster Robotics SDK Build + Install Script
# --------------------------------------------
# Cleans, configures, builds, and installs the SDK + Python bindings.
#

set -Eeuo pipefail
IFS=$'\n\t'

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
log()  { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
err()  { printf "\033[1;31m[ERR ]\033[0m %s\n"  "$*" >&2; }

on_error() {
  err "Script failed at line $1 (command: $2)"
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
SRC_DIR="$(pwd)"
BUILD_DIR="${SRC_DIR}/build"
INSTALL_PREFIX="/usr/local"        # change with -DCMAKE_INSTALL_PREFIX if desired
ENABLE_PYTHON="ON"                 # toggle Python bindings (ON/OFF)

# -------------------------------------------------------------------
# Dependency check
# -------------------------------------------------------------------
log "Installing Python dependencies (pybind11, pybind11-stubgen)..."
if command -v pip3 >/dev/null 2>&1; then
  pip3 install --upgrade pip
  pip3 install --upgrade pybind11 pybind11-stubgen
else
  err "pip3 not found. Please install Python3 and pip3 first."
  exit 1
fi

# -------------------------------------------------------------------
# Clean + prepare
# -------------------------------------------------------------------
log "Cleaning old build dir..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"
cd "${BUILD_DIR}"

# -------------------------------------------------------------------
# Configure with CMake
# -------------------------------------------------------------------
log "Configuring project with CMake..."
cmake .. \
  -DBUILD_PYTHON_BINDING="${ENABLE_PYTHON}" \
  -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}"

# -------------------------------------------------------------------
# Build
# -------------------------------------------------------------------
log "Building with $(nproc) cores..."
make -j"$(nproc)"

# -------------------------------------------------------------------
# Install
# -------------------------------------------------------------------
log "Installing to ${INSTALL_PREFIX}..."
make install

# -------------------------------------------------------------------
# Final message
# -------------------------------------------------------------------
log "✅ Build and installation completed successfully!"