#!/usr/bin/env bash
# Copy this whole kit onto the K1 (or any machine with the Booster SDK).
#
#   ./deploy.sh <user>@<robot-ip>
#
# Example:
#   ./deploy.sh booster@192.168.1.100
#
# After it finishes:
#   ssh <user>@<robot-ip>
#   cd ~/k1_boxing_kit
#   ./run.sh verify
set -euo pipefail

ROBOT="${1:-}"
if [ -z "$ROBOT" ]; then
  echo "Usage: ./deploy.sh <user>@<robot-ip>"
  echo "Example: ./deploy.sh booster@192.168.1.100"
  exit 1
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Copying kit to ${ROBOT}:~/k1_boxing_kit ..."
scp -r "$DIR" "${ROBOT}:~/"

echo ""
echo "Done. Next:"
echo "  ssh ${ROBOT}"
echo "  cd ~/k1_boxing_kit"
echo "  ./run.sh verify        # confirm joints first"
echo "  ./run.sh fight         # then box (slow)"
