#!/usr/bin/env bash
#
# Booster Robotics SDK + third_party installer
# - Detects arch and picks the right lib folder
# - Verifies required tools & packages
# - Copies headers/libs to /usr/local and runs ldconfig
# - Clear logs + error handling
#

set -Eeuo pipefail
IFS=$'\n\t'

#######################################
# Logging helpers
#######################################
log()  { printf "\033[1;34m[INFO]\033[0m %s\n" "$*"; }
warn() { printf "\033[1;33m[WARN]\033[0m %s\n" "$*" >&2; }
err()  { printf "\033[1;31m[ERR ]\033[0m %s\n"  "$*" >&2; }

on_error() {
  err "Script failed at line $1 (command: $2)"
}
trap 'on_error "$LINENO" "$BASH_COMMAND"' ERR

#######################################
# Root check
#######################################
if [[ ${EUID:-$(id -u)} -ne 0 ]]; then
  err "Please run as root (or with sudo)."
  exit 1
fi

#######################################
# Resolve directories
#######################################
# Directory containing this script (resolves symlinks)
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
BOOSTER_SDK_DIR="${SCRIPT_DIR}"
THIRD_PARTY_DIR="${BOOSTER_SDK_DIR}/third_party"

log "Booster Robotics SDK Dir = ${BOOSTER_SDK_DIR}"
log "Third Party Dir          = ${THIRD_PARTY_DIR}"

#######################################
# Detect CPU architecture
#######################################
UNAME_ARCH="$(uname -m)"
case "${UNAME_ARCH}" in
  aarch64|arm64)   ARCH_DIR="aarch64" ;;
  x86_64|amd64)    ARCH_DIR="x86_64"  ;;
  *)               ARCH_DIR="${UNAME_ARCH}"; warn "Unrecognized arch '${UNAME_ARCH}', using '${ARCH_DIR}' as-is." ;;
esac
log "CPU Arch = ${UNAME_ARCH} -> lib subdir = ${ARCH_DIR}"

BOOSTER_LIB_DIR="${BOOSTER_SDK_DIR}/lib/${ARCH_DIR}"
THIRD_PARTY_LIB_DIR="${THIRD_PARTY_DIR}/lib/${ARCH_DIR}"

log "SDK Lib Dir              = ${BOOSTER_LIB_DIR}"
log "Third Party Lib Dir      = ${THIRD_PARTY_LIB_DIR}"

#######################################
# Package manager + dependencies
#######################################
have_cmd() { command -v "$1" >/dev/null 2>&1; }

if have_cmd apt-get; then
  log "Updating apt package lists…"
  apt-get update -y

  # Prefer a single install call (faster, clearer logs)
  DEBS=(
    git
    build-essential
    cmake
    libssl-dev
    libasio-dev
    libtinyxml2-dev
  )

  log "Installing packages: ${DEBS[*]}"
  # Some minimal images lack apt's recommends; keep it simple:
  if ! apt-get install -y "${DEBS[@]}"; then
    err "apt-get install failed. Try 'apt-get update' again or check network/proxy."
    exit 1
  fi
else
  warn "apt-get not found. Skipping package installation. Ensure required deps are installed manually."
fi

#######################################
# Validate source directories
#######################################
missing=0
if [[ ! -d "${BOOSTER_SDK_DIR}/include" ]]; then
  err "Missing: ${BOOSTER_SDK_DIR}/include"
  missing=1
fi
if [[ ! -d "${BOOSTER_LIB_DIR}" ]]; then
  err "Missing: ${BOOSTER_LIB_DIR} (arch-specific libs)"
  missing=1
fi
if [[ ! -d "${THIRD_PARTY_DIR}/include" ]]; then
  warn "Missing: ${THIRD_PARTY_DIR}/include (continuing without third-party headers)"
fi
if [[ ! -d "${THIRD_PARTY_LIB_DIR}" ]]; then
  warn "Missing: ${THIRD_PARTY_LIB_DIR} (continuing without third-party libs)"
fi
if [[ $missing -eq 1 ]]; then
  err "Required SDK directories are missing. Aborting."
  exit 1
fi

#######################################
# Install headers & libraries
#######################################
# Create destinations
install -d /usr/local/include
install -d /usr/local/lib

# Copy SDK headers/libs
log "Installing Booster SDK headers → /usr/local/include"
cp -a "${BOOSTER_SDK_DIR}/include/." /usr/local/include/

log "Installing Booster SDK libs → /usr/local/lib"
cp -a "${BOOSTER_LIB_DIR}/." /usr/local/lib/

log "Booster Robotics SDK installed successfully!"

# Copy third-party (if present)
if [[ -d "${THIRD_PARTY_DIR}/include" ]]; then
  log "Installing third-party headers → /usr/local/include"
  cp -a "${THIRD_PARTY_DIR}/include/." /usr/local/include/
fi

if [[ -d "${THIRD_PARTY_LIB_DIR}" ]]; then
  log "Installing third-party libs → /usr/local/lib"
  cp -a "${THIRD_PARTY_LIB_DIR}/." /usr/local/lib/
fi

log "Third-party libraries installed successfully (if present)."

#######################################
# Refresh linker cache
#######################################
if have_cmd ldconfig; then
  log "Running ldconfig…"
  ldconfig
else
  warn "ldconfig not found; you may need to update the linker cache manually."
fi

log "✅ All done."