@echo off

title JumpscaleX SDK windows packager
echo Creating binary

pip3 install -r requirements.txt
pip3 install staticx

cp InstallTools.py sdk/
pyinstaller 3sdk.spec
rm sdk/InstallTools.py

echo Done! Press any key to continue ...
pause