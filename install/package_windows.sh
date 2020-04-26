export WINEPREFIX="$(pwd)/windows"
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
wine pyinstaller.exe 3sdk.spec
