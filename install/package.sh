#!/usr/bin/env bash
pip3 install --user -r requirements.txt
pyinstaller 3sdk.py --onefile --additional-hooks-dir=./hooks
