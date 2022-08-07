import tarfile
import logging
import lzma
from os.path import basename

from .bcjfilter import get_bcj_filter_arch
from .utils import get_symlink_target, make_mode_executable
from .constants import *
from .errors import *


def get_bcj_filter():
    arch = get_bcj_filter_arch()
    if not arch:
        return None, ''

    # Get the lzma module constant name and value
    filt_name = 'FILTER_' + arch
    filt = getattr(lzma, filt_name)

    return filt, filt_name


def get_xz_filters():
    filters = []

    # Get a BCJ filter for the current architecture
    bcj_filter, bcj_filter_name = get_bcj_filter()
    if bcj_filter:
        logging.info("Using XZ BCJ filter {}".format(bcj_filter_name))
        filters.append(dict(id=bcj_filter))

    # The last filter in the chain must be a compression filter.
    filters.append(dict(id=lzma.FILTER_LZMA2))
    return filters

class SxArchive:
    def __init__(self, fileobj, mode, compress):
        """Create a staticx archive

        Parameters:
        fileobj:    File object for the archive (not closed by this class)
        mode:       Mode: 'r' (for reading) or 'w' (for writing)
        compress:   Boolean: use xz compression or not
        """
        # Keep original fileobj arg for consumer convenience only, never closed
        self.fileobj = fileobj
        self.xzf = None

        if compress:
            self.xzf = lzma.open(
                filename = fileobj,
                mode = mode,
                format = lzma.FORMAT_XZ,

                # Use CRC32 instead of CRC64 (FORMAT_XZ default)
                # Otherwise, enable XZ_USE_CRC64 in libxz/xz_config.h
                check = lzma.CHECK_CRC32,

                filters = get_xz_filters(),
            )

            fileobj = self.xzf

        # Our embedded libtar only supports older GNU format (not new PAX format)
        self.tar = tarfile.open(fileobj=fileobj, mode=mode, format=tarfile.GNU_FORMAT)

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.close()

    def close(self):
        # Don't touch self.fileobj here

        if self.tar:
            self.tar.close()
            self.tar = None

        if self.xzf:
            self.xzf.close()
            self.xzf = None


    def add_symlink(self, name, target):
        """Add a symlink to the archive"""
        if name == target:
            raise ValueError("Refusing to add self-referential symlink")
        t = tarfile.TarInfo()
        t.type = tarfile.SYMTYPE
        t.name = name
        t.linkname = target

        self.tar.addfile(t)

    def add_fileobj(self, name, fileobj):
        logging.info("Adding {}".format(name))
        tarinfo = self.tar.gettarinfo(arcname=name, fileobj=fileobj)
        tarinfo.mode = make_mode_executable(tarinfo.mode)
        self.tar.addfile(tarinfo, fileobj)

    def add_program(self, path, name):
        """Add user program to the archive

        This adds the user program to the archive using its original filename.
        Additionally, a symlink to the program is created with a fixed name to
        enable the bootloader to identify the program to execute.

        Parameters:
        path:   The path to the program to add
        name:   The original filename of the program

        Should only be called once. TODO: Enforce this.
        """
        def make_exec(tarinfo):
            tarinfo.mode = make_mode_executable(tarinfo.mode)
            return tarinfo

        logging.info("Adding {} as {}".format(path, name))
        self.tar.add(path, arcname=name, filter=make_exec)

        # Store a link to the program so the bootloader knows what to execute
        self.add_symlink(PROG_FILENAME, name)

    def add_file(self, path, arcname=None):
        self.tar.add(path, arcname=arcname)

    def add_interp_symlink(self, interp):
        """Add symlink for ld.so interpreter"""
        self.add_symlink(INTERP_FILENAME, basename(interp))
