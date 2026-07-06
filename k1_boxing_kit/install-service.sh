#!/usr/bin/env bash
# Install boxing as an autostart service ON THE ROBOT.
# After this, you never need the laptop again: power on Adam, stand him up
# (STAND then WLAK buttons), and boxing activates automatically. Use the remote.
#
# SAFE + REVERSIBLE: this ONLY adds one new file (/etc/systemd/system/k1-boxing.service).
# It does NOT modify any of Booster's own code or config. Remove it completely with:
#     ./uninstall-service.sh
#
# Run this ON the robot, once:
#   cd ~/himpublic/k1_boxing_kit
#   ./install-service.sh
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"
PY="$(command -v python3 || command -v python || true)"
if [ -z "$PY" ]; then
  echo "ERROR: python3 not found. Run this on the robot."
  exit 1
fi

SERVICE=/etc/systemd/system/k1-boxing.service
if [ -e "$SERVICE" ]; then
  echo "Note: $SERVICE already exists - it will be overwritten."
fi

echo "Installing service -> $SERVICE"
echo "  dir:  $DIR"
echo "  user: $USER_NAME"
echo "  py:   $PY"
echo "(This is the ONLY file created. Nothing else on the robot is changed.)"

# Restart=no on purpose: if anything goes wrong it just STOPS (predictable),
# it does not loop or fight you. You restart it deliberately.
sudo tee "$SERVICE" >/dev/null <<EOF
[Unit]
Description=K1 Boxing (remote-controlled, hands-free)
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$DIR
ExecStart=$PY -m k1_boxing --auto
Restart=no

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable k1-boxing.service
sudo systemctl restart k1-boxing.service

echo ""
echo "Done. Boxing auto-starts on boot (and is running now)."
echo "It WAITS until you stand Adam up (STAND then WLAK), then activates - safe."
echo ""
echo "=== HOW TO STOP / REMOVE (save these) ==="
echo "Stop now .............: sudo systemctl stop k1-boxing"
echo "Never start again .....: sudo systemctl disable k1-boxing"
echo "REMOVE COMPLETELY .....: ./uninstall-service.sh"
echo "Watch its logs ........: journalctl -u k1-boxing -f"
echo "Emergency limp (robot) : LT + BACK on the controller, or F1 on the back panel"
