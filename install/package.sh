#!/usr/bin/env bash
set -e
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    pip3 install staticx
    pip3 uninstall pyinstaller
    pip3 install https://github.com/pyinstaller/pyinstaller/archive/develop.zip
    if [ "$(whoami)" == "root" ]; then
        pip3 install -r requirements.txt
    else
        pip3 install --user -r requirements.txt
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac OSX
    brew install upx
fi


cp InstallTools.py sdk/
pyinstaller 3sdk.spec
rm sdk/InstallTools.py
#--onefile --additional-hooks-dir=./hooks
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    mv dist/3sdk dist/3sdkdynamic
    staticx dist/3sdkdynamic dist/3sdk
fi
