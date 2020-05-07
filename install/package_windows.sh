#!/bin/bash
set -e
version=$(git describe --tags)
if ! which wine > /dev/null; then
    echo "Please install wine and try again"
    exit 1
fi
export WINEPREFIX="$(pwd)/windows"
export WINEDLLOVERRIDES="mscoree,mshtml="
mkdir -p "${WINEPREFIX}"
PYTHONURL="https://www.python.org/ftp/python/3.7.7/python-3.7.7-amd64.exe"
PYTHONSETUP="${WINEPREFIX}/python-setup.exe"
if ! wine pip3.exe -v > /dev/null; then
    if [ ! -e "${PYTHONSETUP}" ]; then
        wget -O "${PYTHONSETUP}" "${PYTHONURL}"
    fi
    wine "$PYTHONSETUP" /quiet InstallAllUsers=1 PrependPath=1
fi
wine pip3.exe install -r requirements.txt
sed -i "s/_unreleased_/${version}/" threesdk/__init__.py
wine pyinstaller.exe 3sdk.spec
git checkout threesdk/__init__.py
cp dist/3sdk.exe "dist/3sdk_${version}_windows.exe"
