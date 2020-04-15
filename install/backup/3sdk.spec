# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['3sdk.py'],
             pathex=['/tmp'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['./hooks'],
             runtime_hooks=[],
             excludes=["tcl","win32com","jinja2","zmq","PyQt5","cElementTree","tkinter",
                "lib2to3","PyQt4","numpy","notebook","matplotlib",
                "nbformat","cairo","jsonschema","graphviz",
                'scipy','PIL','cython',
                ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='3sdk',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=/tmp,
          console=True )
