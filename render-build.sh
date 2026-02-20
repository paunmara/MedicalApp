#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt

echo "Installing system libraries..."
apt-get update || true
apt-get install -y libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 libffi-dev libjpeg-dev libopenjp2-7-dev || true