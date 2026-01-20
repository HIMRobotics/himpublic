#!/bin/bash
set -e

SERVICE_SRC="./fight-mode.service"
SERVICE_NAME=$(basename "$SERVICE_SRC")
SERVICE_DIR="$HOME/.config/systemd/user"

echo "[INFO] Installing fight-mode service for user: $USER"

# --- Validate and copy ---
if [ ! -f "$SERVICE_SRC" ]; then
    echo "[ERROR] Service file not found: $SERVICE_SRC"
    exit 1
fi

mkdir -p "$SERVICE_DIR"
cp "$SERVICE_SRC" "$SERVICE_DIR/$SERVICE_NAME"

echo "[INFO] Installed: $SERVICE_DIR/$SERVICE_NAME"

# --- Enable & start for user ---
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME"
systemctl --user restart "$SERVICE_NAME"

echo "[INFO] Service enabled and started for user $USER"

# --- Optional linger setup ---
read -p "Enable linger (auto-start even without login)? [y/N]: " choice
if [[ "$choice" =~ ^[Yy]$ ]]; then
    sudo loginctl enable-linger "$USER"
    echo "[INFO] Linger enabled — fight-mode starts automatically on boot."
else
    echo "[INFO] Linger not enabled — fight-mode starts only after login."
fi

echo "[SUCCESS] fight-mode service installed!"
echo "Check status with: systemctl --user status $SERVICE_NAME"