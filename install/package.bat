@echo off

title JumpscaleX SDK windows packager
echo Creating binary

pip install -r requirements.txt
pip install staticx
pip install pypiwin32

cp InstallTools.py sdk/
pyinstaller 3sdk.spec
rm sdk/InstallTools.py

echo Done! Press any key to continue ...
pause