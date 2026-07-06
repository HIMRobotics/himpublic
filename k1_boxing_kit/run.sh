#!/usr/bin/env bash
# Run K1 boxing. Use ON the robot (after deploy.sh), or wherever the Booster SDK
# is installed.
#
#   ./run.sh verify           # read-only: confirm arm joint indices (no motion)
#   ./run.sh fight            # fight mode, slow speed (safe default)
#   ./run.sh fight medium     # fight mode, medium speed (only after tuning!)
#   ./run.sh capture NAME     # backup: record poses by hand (read-only, DAMP)
#
# Network interface defaults to 127.0.0.1 (running on the robot). Override with:
#   IFACE=<interface> ./run.sh fight
set -euo pipefail
cd "$(dirname "$0")"

MODE="${1:-verify}"
SPEED="${2:-slow}"
IFACE="${IFACE:-127.0.0.1}"

case "$MODE" in
  verify)
    exec python3 -m k1_boxing --verify-joints --network-interface "$IFACE"
    ;;
  fight)
    exec python3 -m k1_boxing --speed "$SPEED" --network-interface "$IFACE"
    ;;
  capture)
    # Second arg is the pose name here (e.g. ./run.sh capture LEFT_PUNCH).
    exec python3 -m k1_boxing.capture --name "${2:-MY_POSE}" --network-interface "$IFACE"
    ;;
  *)
    echo "Usage: ./run.sh [verify|fight|capture] [slow|medium|fast | POSE_NAME]"
    exit 1
    ;;
esac
