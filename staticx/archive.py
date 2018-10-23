import tarfile
import logging
from os.path import basename, islink

try:
    # Python 3
    import lzma
    lzma.open       # pyliblzma doesn't have lzma.open()
except (ImportError, AttributeError):
    # Python 2.7
    from backports import lzma

from .bcjfilter import get_bcj_filter_arch
from .utils import get_symlink_target
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

class SxArchive(object):
    def __init__(self, fileobj, mode, compress):
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

        self.tar = tarfile.open(fileobj=fileobj, mode=mode)
        self._added_libs = []

    def __enter__(self):
        return self

    def __exit__(self, *excinfo):
        self.tar.close()
        if self.xzf:
            self.xzf.close()


    @property
    def libraries(self):
        return iter(self._added_libs)

    def add_symlink(self, name, target):
        """Add a symlink to the archive"""
        t = tarfile.TarInfo()
        t.type = tarfile.SYMTYPE
        t.name = name
        t.linkname = target

        self.tar.addfile(t)

    def add_program(self, path):
        """Add user program to the archive

        The program will be added with a fixed name.
        Should only be called once. TODO: Enforce this.
        """
        arcname = PROG_FILENAME
        logging.info("Adding {} as {}".format(path, arcname))
        self.tar.add(path, arcname=arcname)

    def add_library(self, path):
        """Add a library to the archive

        The library will be added with its base name.
        Symlinks will also be added and followed.
        """

        if basename(path) in self._added_libs:
            raise LibExistsError(basename(path))

        # 'recursively' step through any symbolic links, generating local links inside the archive
        linklib = path
        while islink(linklib):
            arcname = basename(linklib)
            linklib = get_symlink_target(linklib)

            # add a symlink.  at this point the target probably doesn't exist, but that doesn't matter yet
            logging.info("    Adding Symlink {} => {}".format(arcname, basename(linklib)))
            self.add_symlink(arcname, basename(linklib))
            self._added_libs.append(arcname)

        # left with a real file at this point, add it to the archive.
        arcname = basename(linklib)
        logging.info("    Adding {} as {}".format(linklib, arcname))
        self.tar.add(linklib, arcname=arcname)
        self._added_libs.append(arcname)

    def add_interp_symlink(self, interp):
        """Add symlink for ld.so interpreter"""
        self.add_symlink(INTERP_FILENAME, basename(interp))
