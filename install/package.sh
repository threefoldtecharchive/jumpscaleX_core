#!/usr/bin/env bash

pyinstaller 3sdk.py --onefile --additional-hooks-dir=./hooks
