import os
import logging
import tempfile

from ..elf import get_shobj_deps, is_dynamic, LddError
from ..utils import make_executable, mkdirs_for

def process_pyinstaller_archive(sx):
    # See utils/cliutils/archive_viewer.py

    # If PyInstaller is not installed, do nothing
    try:
        from PyInstaller.archive.readers import CArchiveReader, NotAnArchiveError
    except ImportError:
        return

    # Attempt to open the program as PyInstaller archive
    try:
        pyi_ar = CArchiveReader(sx.orig_prog)
    except:
        # Silence all PyInstaller exceptions here
        return
    logging.info("Opened PyInstaller archive!")

    with PyInstallHook(sx, pyi_ar) as h:
        h.process()



class PyInstallHook:
    def __init__(self, sx, pyi_archive):
        self.sx = sx
        self.pyi_ar = pyi_archive

        self.tmpdir = tempfile.TemporaryDirectory(prefix='staticx-pyi-')


    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.tmpdir.cleanup()


    def process(self):
        binaries = self._extract_binaries()
        for binary in binaries:
            # These could be Python libraries, shared object dependencies, or
            # anything else a user might add via `binaries` in the .spec file.
            self._add_required_deps(binary)


    def _extract_binaries(self):
        result = []

        for n, item in enumerate(self.pyi_ar.toc.data):
            (dpos, dlen, ulen, flag, typcd, name) = item

            # Only process binary files
            # See xformdict in PyInstaller.building.api.PKG
            if typcd != 'b':
                continue

            # Extract it to a temporary location
            _, data = self.pyi_ar.extract(n)
            tmppath = os.path.join(self.tmpdir.name, name)
            logging.debug("Extracting to {}".format(tmppath))
            mkdirs_for(tmppath)
            with open(tmppath, 'wb') as f:
                f.write(data)

            # Silence "you do not have execution permission" warning from ldd
            make_executable(tmppath)

            # We can't use yield here, because we need all of the libraries to be
            # extracted prior to running ldd (see #61)
            result.append(tmppath)

        return result


    def _add_required_deps(self, lib):
        """Add dependencies of lib to staticx archive"""

        # Verify this is a shared library
        if not is_dynamic(lib):
            # It's okay if there's a static executable in the PyInstaller
            # archive. See issue #78
            return

        # Check for RPATH/RUNPATH, but only "dangerous" values and let
        # "harmless" values pass (e.g. "$ORIGIN/cffi.libs")
        self.sx.check_library_rpath(lib, dangerous_only=True)
        # Unfortunately, there's no easy way to fix an UnsupportedRunpathError
        # here, because staticx is not about to to modify the library and
        # re-pack the PyInstaller archive itself.

        # Try to get any dependencies of this file
        try:
            deps = get_shobj_deps(lib, libpath=[self.tmpdir.name])
        except LddError as e:
            # In certain cases, ldd might get upset about binary files
            # (probably added by the user via .spec file). This can happen
            # e.g., if a dynamically-linked musl-libc application is included.
            # There's a reasonable chance this won't run, but it's not really
            # staticx's problem, so warn the user and go on.
            logging.warning(e)
            return


        # Add any missing libraries to our archive
        for deppath in deps:
            dep = os.path.basename(deppath)

            if self.pyi_ar.toc.find(dep) != -1:
                logging.debug("{} already in pyinstaller archive".format(dep))
                continue

            self.sx.add_library(deppath, exist_ok=True)
