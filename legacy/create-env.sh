#!/bin/bash
set -e
python3 -m venv .venv --system-site-packages # use system packages to get booster sdk
source .venv/bin/activate
pip install -r requirements.txt