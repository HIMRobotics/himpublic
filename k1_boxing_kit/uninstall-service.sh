#!/usr/bin/env bash
# Completely remove the boxing autostart service from the robot.
# Safe to run anytime, even if it's not installed. Leaves the robot exactly as it
# was before install-service.sh (only removes /etc/systemd/system/k1-boxing.service).
#
#   cd ~/himpublic/k1_boxing_kit
#   ./uninstall-service.sh
set -euo pipefail

SERVICE=/etc/systemd/system/k1-boxing.service

echo "Stopping boxing service (if running)..."
sudo systemctl stop k1-boxing.service 2>/dev/null || true

echo "Disabling boot autostart (if enabled)..."
sudo systemctl disable k1-boxing.service 2>/dev/null || true

if [ -e "$SERVICE" ]; then
  echo "Removing $SERVICE ..."
  sudo rm -f "$SERVICE"
else
  echo "No service file found (already removed)."
fi

sudo systemctl daemon-reload
sudo systemctl reset-failed k1-boxing.service 2>/dev/null || true

echo ""
echo "Done. The autostart service is fully removed."
echo "Nothing else on the robot was changed. Boxing will NOT start on boot anymore."
echo "You can still run it manually with:  ./run.sh fight-standing"
