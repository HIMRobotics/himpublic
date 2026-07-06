#!/usr/bin/env bash
# Run K1 boxing. Use ON the robot (after cloning the repo there).
#
#   ./run.sh check            # START HERE: checks data link, mode, and remote
#   ./run.sh verify           # read-only: confirm arm joint indices (no motion)
#   ./run.sh remote           # read-only: check the remote controller is connected
#   ./run.sh fight            # fight mode, slow speed (safe default)
#   ./run.sh fight medium     # fight mode, medium speed (only after tuning!)
#   ./run.sh fight-standing   # fight mode when Adam is ALREADY standing (buttons/app)
#   ./run.sh capture NAME     # backup: record poses by hand (read-only, DAMP)
#
# Network interface defaults to 127.0.0.1 (running on the robot). Override with:
#   IFACE=<interface> ./run.sh fight
set -euo pipefail
cd "$(dirname "$0")"

# --- friendly environment checks -------------------------------------------
PY="python3"
if ! command -v "$PY" >/dev/null 2>&1; then
  if command -v python >/dev/null 2>&1; then
    PY="python"
  else
    echo "ERROR: python3 is not installed on this machine."
    echo "Run this ON the robot (that's where the Booster SDK lives)."
    exit 1
  fi
fi

if [ ! -d "k1_boxing" ]; then
  echo "ERROR: can't find the k1_boxing folder next to this script."
  echo "Make sure you're in the k1_boxing_kit directory:  cd ~/himpublic/k1_boxing_kit"
  exit 1
fi

MODE="${1:-check}"          # no argument -> run the health check
SPEED="${2:-slow}"
IFACE="${IFACE:-127.0.0.1}"

case "$MODE" in
  check)
    exec "$PY" -m k1_boxing --check --network-interface "$IFACE"
    ;;
  verify)
    exec "$PY" -m k1_boxing --verify-joints --network-interface "$IFACE"
    ;;
  remote)
    exec "$PY" -m k1_boxing --test-remote --network-interface "$IFACE"
    ;;
  fight)
    exec "$PY" -m k1_boxing --speed "$SPEED" --network-interface "$IFACE"
    ;;
  fight-standing)
    # Use when you already stood Adam up with the STAND + WALK buttons (or app).
    exec "$PY" -m k1_boxing --speed "$SPEED" --already-standing --network-interface "$IFACE"
    ;;
  capture)
    # Second arg is the pose name here (e.g. ./run.sh capture LEFT_PUNCH).
    exec "$PY" -m k1_boxing.capture --name "${2:-MY_POSE}" --network-interface "$IFACE"
    ;;
  -h|--help|help)
    echo "Usage: ./run.sh [check|verify|remote|fight|fight-standing|capture] [slow|medium|fast | POSE_NAME]"
    echo "Start with:  ./run.sh check"
    ;;
  *)
    echo "Unknown command: $MODE"
    echo "Usage: ./run.sh [check|verify|remote|fight|fight-standing|capture] [slow|medium|fast | POSE_NAME]"
    echo "Start with:  ./run.sh check"
    exit 1
    ;;
esac
