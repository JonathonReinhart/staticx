import os
import logging
import tempfile

from ..elf import get_shobj_deps, is_dynamic_elf, LddError
from ..errors import Error, UnsupportedRpathError, UnsupportedRunpathError
from ..utils import make_executable, mkdirs_for


def process_pyinstaller_archive(sx):
    # See utils/cliutils/archive_viewer.py

    # If PyInstaller is not installed, do nothing
    try:
        import PyInstaller
    except ImportError:
        logging.info("PyInstaller not installed; skipping hook")
        return
    from PyInstaller.archive.readers import CArchiveReader

    logging.info("Using PyInstaller version %s", PyInstaller.__version__)
    pyi_version = tuple(int(x) for x in PyInstaller.__version__.split("."))

    # Attempt to open the program as PyInstaller archive
    try:
        pyi_ar = CArchiveReader(sx.orig_prog)
    except:
        # Silence all PyInstaller exceptions here
        return
    logging.info("Opened PyInstaller archive!")

    # Refuse to process files if running PyInstaller 4.1 - 4.2.
    # This assumes that the current version of PyInstaller was the same one
    # used to build the input file. This isn't necessarily the case, but likely
    # enough to detect this way.
    # We do this after opening the archive to avoid failing for non-pyinstalled
    # input files.
    if pyi_version[:2] in ((4, 1), (4, 2)):
        msg = f"PyInstaller v{PyInstaller.__version__} is unsupported\n"
        msg += "(See https://github.com/JonathonReinhart/staticx/issues/170)"
        raise Error(msg)

    if pyi_version < (5, 10, 0):
        # Adapt the CArchiveReader from PyInstaller before 5.10
        # to the new 5.10+ API.
        pyi_ar = CArchiveReaderPre510Adapter(pyi_ar)

    with PyInstallHook(sx, pyi_ar) as h:
        h.process()


class PyInstallHook:
    def __init__(self, sx, pyi_archive):
        self.sx = sx
        self.pyi_ar = pyi_archive

        self.tmpdir = tempfile.TemporaryDirectory(prefix="staticx-pyi-")

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.tmpdir.cleanup()

    def process(self):
        binaries = self._extract_binaries()

        # These could be Python libraries, shared object dependencies, or
        # anything else a user might add via `binaries` in the .spec file.
        # Filter out everything except dynamic ELFs
        binaries = [b for b in binaries if is_dynamic_elf(b)]

        self._audit_libs(binaries)

        for binary in binaries:
            self._add_required_deps(binary)

    def _extract_binaries(self):
        result = []

        for name, item in self.pyi_ar.toc.items():
            (dpos, dlen, ulen, flag, typcd) = item

            # Only process binary files
            # See xformdict in PyInstaller.building.api.PKG
            if typcd != "b":
                continue

            # Extract it to a temporary location
            data = self.pyi_ar.extract(name)
            tmppath = os.path.join(self.tmpdir.name, name)
            logging.debug(f"Extracting to {tmppath}")
            mkdirs_for(tmppath)
            with open(tmppath, "wb") as f:
                f.write(data)

            # Silence "you do not have execution permission" warning from ldd
            make_executable(tmppath)

            # We can't use yield here, because we need all of the libraries to be
            # extracted prior to running ldd (see #61)
            result.append(tmppath)

        return result

    def _audit_libs(self, libs):
        """Audit the dynamic libraries included in the PyInstaller archive"""
        errors = []
        for lib in libs:
            # Check for RPATH/RUNPATH, but only "dangerous" values and let
            # "harmless" values pass (e.g. "$ORIGIN/cffi.libs")
            try:
                self.sx.check_library_rpath(lib, dangerous_only=True)
            except (UnsupportedRpathError, UnsupportedRunpathError) as e:
                # Unfortunately, there's no easy way to fix an UnsupportedRunpathError
                # here, because staticx is not about to to modify the library and
                # re-pack the PyInstaller archive itself.
                errors.append(e)

        if errors:
            msg = "Unsupported PyInstaller input\n\n"
            msg += "One or more libraries included in the PyInstaller"
            msg += " archive uses unsupported RPATH/RUNPATH tags:\n\n"
            for err in errors:
                msg += f"  {err.libpath}: {err.tag}={err.value!r}\n"
            msg += "\nSee https://github.com/JonathonReinhart/staticx/issues/188"
            raise Error(msg)

    def _add_required_deps(self, lib):
        """Add dependencies of lib to staticx archive"""

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

            if dep in self.pyi_ar.toc:
                logging.debug(f"{dep} already in pyinstaller archive")
                continue

            self.sx.add_library(deppath, exist_ok=True)


class CArchiveReaderPre510Adapter:
    """Adapts a pre-5.10 CArchiveReader to 5.10+ API"""

    def __init__(self, old_archive):
        self._old_archive = old_archive

        self.toc = {
            name: tuple(entry) for *entry, name in self._old_archive.toc.data
        }

    def extract(self, name):
        _, data = self._old_archive.extract(name)
        return data
