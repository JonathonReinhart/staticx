import os
import logging
import shutil
import tempfile

from ..elf import get_shobj_deps
from ..utils import make_executable, mkdirs_for

def process_pyinstaller_archive(ar, prog):
    # See utils/cliutils/archive_viewer.py

    # If PyInstaller is not installed, do nothing
    try:
        from PyInstaller.archive.readers import CArchiveReader, NotAnArchiveError
    except ImportError:
        return

    # Attempt to open the program as PyInstaller archive
    try:
        pyi_ar = CArchiveReader(prog)
    except:
        # Silence all PyInstaller exceptions here
        return
    logging.info("Opened PyInstaller archive!")

    # Create a temporary directory
    # TODO PY3: Use tempfile.TemporaryDirectory and cleanup()
    tmpdir = tempfile.mkdtemp(prefix='staticx-pyi-')

    try:
        # Process the archive, looking at all shared libs
        for n, item in enumerate(pyi_ar.toc.data):
            (dpos, dlen, ulen, flag, typcd, name) = item

            # Only process binary files
            # See xformdict in PyInstaller.building.api.PKG
            if typcd != 'b':
                continue

            # Extract it to a temporary location
            x, data = pyi_ar.extract(n)
            tmppath = os.path.join(tmpdir, name)
            logging.debug("Extracting to {}".format(tmppath))
            mkdirs_for(tmppath)
            with open(tmppath, 'wb') as f:
                f.write(data)

            # Silence "you do not have execution permission" warning from ldd
            make_executable(tmppath)

            # Add any missing libraries to our archive
            for libpath in get_shobj_deps(tmppath):
                lib = os.path.basename(libpath)

                if lib in ar.libraries:
                    logging.debug("{} already in staticx archive".format(lib))
                    continue

                if pyi_ar.toc.find(lib) != -1:
                    logging.debug("{} already in pyinstaller archive".format(lib))
                    continue

                ar.add_library(libpath)
    finally:
        shutil.rmtree(tmpdir)
