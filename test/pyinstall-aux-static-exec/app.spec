a = Analysis(['app.py'],
             binaries=[
                 ('aux-dynamic', '.'),
                 ('aux-static', '.'),
             ],
             datas=[],
             excludes=[],
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='app',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
