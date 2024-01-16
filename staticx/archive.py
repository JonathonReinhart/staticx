from __future__ import annotations
import dataclasses
import tarfile
import logging
import lzma
from os.path import basename
from types import TracebackType
from typing import Dict, List, IO, Optional, Type, Union
from typing_extensions import Literal

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import StrPath

from .bcjfilter import get_bcj_filter_arch
from .utils import get_symlink_target, make_mode_executable
from .constants import *
from .errors import *

@dataclasses.dataclass
class BcjFilter:
    id: int
    name: str


def get_bcj_filter() -> Optional[BcjFilter]:
    arch = get_bcj_filter_arch()
    if not arch:
        return None

    # Get the lzma module constant name and value
    filt_name = 'FILTER_' + arch
    return BcjFilter(
        id=getattr(lzma, filt_name),
        name=filt_name,
    )

LzmaFilterChain = List[Dict[str, Union[str, int]]]

def get_xz_filters() -> List[Dict[str, Union[str, int]]]:
    filters: LzmaFilterChain = []

    # Get a BCJ filter for the current architecture
    bcj_filter = get_bcj_filter()
    if bcj_filter:
        logging.info(f"Using XZ BCJ filter {bcj_filter.name}")
        filters.append(dict(id=bcj_filter.id))

    # The last filter in the chain must be a compression filter.
    filters.append(dict(id=lzma.FILTER_LZMA2))
    return filters

class SxArchive:
    fileobj: IO[bytes]
    xzf: Optional[lzma.LZMAFile]
    tar: tarfile.TarFile

    def __init__(self, fileobj: IO[bytes], mode: Literal["r", "w"], compress: bool):
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
            xzf = lzma.open(
                filename = fileobj,
                mode = mode,
                format = lzma.FORMAT_XZ,

                # Use CRC32 instead of CRC64 (FORMAT_XZ default)
                # Otherwise, enable XZ_USE_CRC64 in libxz/xz_config.h
                check = lzma.CHECK_CRC32,

                filters = get_xz_filters(),
            )
            assert isinstance(xzf, lzma.LZMAFile)
            self.xzf = xzf
            fileobj = xzf

        # Our embedded libtar only supports older GNU format (not new PAX format)
        self.tar = tarfile.open(fileobj=fileobj, mode=mode, format=tarfile.GNU_FORMAT)

    def __enter__(self) -> SxArchive:
        return self

    def __exit__(self,
                 type: Optional[Type[BaseException]],
                 value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        self.close()

    def close(self) -> None:
        # Don't touch self.fileobj here
        self.tar.close()
        if self.xzf:
            self.xzf.close()

    def add_symlink(self, name: str, target: str) -> None:
        """Add a symlink to the archive"""
        if name == target:
            raise ValueError("Refusing to add self-referential symlink")
        t = tarfile.TarInfo()
        t.type = tarfile.SYMTYPE
        t.name = name
        t.linkname = target

        self.tar.addfile(t)

    def add_fileobj(self, name: str, fileobj: IO[bytes]) -> None:
        logging.info(f"Adding {name}")
        tarinfo = self.tar.gettarinfo(arcname=name, fileobj=fileobj)
        tarinfo.mode = make_mode_executable(tarinfo.mode)
        self.tar.addfile(tarinfo, fileobj)

    def add_program(self, path: StrPath, name: str) -> None:
        """Add user program to the archive

        This adds the user program to the archive using its original filename.
        Additionally, a symlink to the program is created with a fixed name to
        enable the bootloader to identify the program to execute.

        Parameters:
        path:   The path to the program to add
        name:   The original filename of the program

        Should only be called once. TODO: Enforce this.
        """
        def make_exec(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo:
            tarinfo.mode = make_mode_executable(tarinfo.mode)
            return tarinfo

        logging.info(f"Adding {path} as {name}")
        self.tar.add(path, arcname=name, filter=make_exec)

        # Store a link to the program so the bootloader knows what to execute
        self.add_symlink(PROG_FILENAME, name)

    def add_file(self, path: StrPath, arcname: Optional[StrPath] = None) -> None:
        self.tar.add(path, arcname=arcname)

    def add_interp_symlink(self, interp: str) -> None:
        """Add symlink for ld.so interpreter"""
        self.add_symlink(INTERP_FILENAME, basename(interp))
