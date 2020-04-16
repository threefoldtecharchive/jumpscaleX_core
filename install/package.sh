#!/usr/bin/env bash
set -e
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    requiredbins=(upx patchelf pip3)
    for requiredbin in ${requiredbins[@]}; do
        if ! which $requiredbin &> /dev/null; then
            echo "Missing dependency '$requiredbin' please install"
            exit 1
        fi
    done
    if [ "$(whoami)" == "root" ]; then
        pip3 install -r requirements.txt
        pip3 install staticx
    else
        pip3 install --user -r requirements.txt
        pip3 install --user staticx
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac OSX
    brew install upx
fi

#cp InstallTools.py threesdk/
pyinstaller 3sdk.spec
#rm threesdk/InstallTools.py
#--onefile --additional-hooks-dir=./hooks
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    # on linux we want to build a static binary to avoid libc issues
    mv dist/3sdk dist/3sdkdynamic
    staticx dist/3sdkdynamic dist/3sdk
fi
