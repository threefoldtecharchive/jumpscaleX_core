#!/usr/bin/env bash

pip3 uninstall pyinstaller
pip3 install https://github.com/pyinstaller/pyinstaller/archive/develop.zip

brew install upx

pyinstaller