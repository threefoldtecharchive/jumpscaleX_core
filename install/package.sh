#!/usr/bin/env bash
set -e

#pip3 uninstall pyinstaller
#pip3 install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
#brew install upx

#if [ "$(whoami)" == "root" ]; then
#    pip3 install -r requirements.txt
#else
#    pip3 install --user -r requirements.txt
#fi
pyinstaller 3sdk.spec
#--onefile --additional-hooks-dir=./hooks
