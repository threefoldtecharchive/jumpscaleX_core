#!/bin/bash
set -e
version=$(git describe --tags)
if ! which wine > /dev/null; then
    echo "Please install wine and try again"
    exit 1
fi
export WINEPREFIX="$(pwd)/windows"
export WINEPATH="${WINEPREFIX}/drive_c/Program Files (x86)/NSIS"
export WINEDLLOVERRIDES="mscoree,mshtml="
mkdir -p "${WINEPREFIX}"
PYTHONURL="https://www.python.org/ftp/python/3.7.7/python-3.7.7-amd64.exe"
NSISURL="https://netix.dl.sourceforge.net/project/nsis/NSIS%203/3.05/nsis-3.05-setup.exe"
PYTHONSETUP="${WINEPREFIX}/python-setup.exe"
NSISSETUP="${WINEPREFIX}/nsis-3.05-setup.exe"
if ! wine pip3.exe -v > /dev/null; then
    if [ ! -e "${PYTHONSETUP}" ]; then
        wget -O "${PYTHONSETUP}" "${PYTHONURL}"
    fi
    wine "$PYTHONSETUP" /quiet InstallAllUsers=1 PrependPath=1
fi

if ! wine makensis.exe > /dev/null; then
    if [ ! -e "${NSISSETUP}" ]; then
        wget -O "${NSISSETUP}" "${NSISURL}"
    fi
    wine "$NSISSETUP" /S InstallAllUsers=1 PrependPath=1
fi

wine pip3.exe install -r requirements.txt
sed -i "s/_unreleased_/${version}/" threesdk/__init__.py
sed -i "s/_unreleased_/${version}/" 3sdk_nsis.nsi
wine pyinstaller.exe 3sdk.spec
wine makensis.exe 3sdk_nsis.nsi
git checkout threesdk/__init__.py 3sdk_nsis.nsi

cp dist/3sdk.exe "dist/3sdk_${version}_windows.exe"
