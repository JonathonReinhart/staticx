import os
import sys

# Add the diretory of the .spec file to the python path
specdir = os.path.abspath(SPECPATH)
sys.path.append(specdir)

from auxlist import aux_apps

# Add whichever binaries were compiled
binaries = [(b, '.') for b in aux_apps if os.path.isfile(b)]

a = Analysis(['app.py'],
             binaries=binaries,
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
