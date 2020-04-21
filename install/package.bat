@echo off

title JumpscaleX SDK windows packager
echo Creating binary

pip install -r requirements.txt
pip install staticx
pip install pypiwin32

pyinstaller 3sdk.spec

echo Done! Press any key to continue ...
pause
