#!/usr/bin/env bash
set -e
if [ "$(whoami)" == "root" ]; then
    pip3 install -r requirements.txt
else
    pip3 install --user -r requirements.txt
fi
pyinstaller 3sdk.py --onefile --additional-hooks-dir=./hooks
