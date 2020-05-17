@echo off

title JumpscaleX SDK windows packager
echo Creating binary

pip install -r requirements.txt
pip install staticx
pip install pypiwin32

pyinstaller 3sdk.spec

REM Create NSIS
powershell.exe -command "& Invoke-WebRequest https://netix.dl.sourceforge.net/project/nsis/NSIS%203/3.05/nsis-3.05-setup.exe -O nsis-3.05-setup.exe"
C:\Users\%USERNAME%\nsis-3.05-setup.exe /S
SET PATH=%PATH%;C:\Program Files (x86)\NSIS
makensis 3sdk_nsis.nsi

echo Done! Press any key to continue ...
pause
