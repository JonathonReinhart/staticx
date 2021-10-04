# PyInstaller spec file

binaries = [('shlib.so', '.')]

a = Analysis(['app.py'], binaries=binaries)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='app',
          )
