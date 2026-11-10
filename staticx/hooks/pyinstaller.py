from __future__ import annotations

import argparse
import contextlib
import dataclasses
import logging
import os
import struct
import tempfile
import zlib
from collections.abc import Iterable
from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING

from ..elf import ELFFileX, LddError, get_shobj_deps, is_dynamic_elf, remove_rpath
from ..errors import Error, UnsupportedRpathError, UnsupportedRunpathError
from ..utils import Pathlike, align_up, get_env_flag, make_executable, mkdirs_for

if TYPE_CHECKING:
    from ..api import StaticxGenerator


def process_pyinstaller_archive(sx: StaticxGenerator) -> None:
    # Attempt to open the program as PyInstaller archive
    try:
        pyi_ar = ArchiveReader.open_elf(sx.orig_prog)
    except Exception as err:
        # TODO: more specific (ELF)
        logging.debug(f"Could not open PyInstaller archive: {err}")
        return
    logging.info("Opened PyInstaller archive!")

    with PyInstallHook(
        sx,
        pyi_ar,
        enable_archive_rewrite=get_env_flag(
            "STATICX_ENABLE_PYINSTALLER_ARCHIVE_REWRITE"
        ),
    ) as h:
        h.process()


class PyInstallHook:
    def __init__(
        self,
        sx: StaticxGenerator,
        pyi_archive: ArchiveReader,
        enable_archive_rewrite: bool = False,
    ):
        self.sx = sx
        self.pyi_ar = pyi_archive
        self.enable_archive_rewrite = enable_archive_rewrite

        self._tmpdir = tempfile.TemporaryDirectory(prefix="staticx-pyi-")

    def __enter__(self) -> PyInstallHook:
        return self

    def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._tmpdir.cleanup()

    @property
    def workdir(self) -> Path:
        return Path(self._tmpdir.name)

    def process(self) -> None:
        logging.debug("Extracting binaries")
        binaries = self._extract_binaries()
        logging.debug(f"Extracted {len(binaries)} binaries")

        # These could be Python libraries, shared object dependencies, or
        # anything else a user might add via `binaries` in the .spec file.
        # Filter out everything except dynamic ELFs
        binaries = [b for b in binaries if is_dynamic_elf(b)]
        logging.debug(f"Found {len(binaries)} dynamic ELF files")

        logging.debug("Auditing libs")
        rewritten_libs = self._audit_libs(binaries)

        logging.debug("Adding deps")
        for binary in binaries:
            self._add_required_deps(binary)

        # Rebuild the PyInstaller archive if necessary
        # (e.g. because library RPATH/RUNPATH were rewritten).
        if rewritten_libs:
            assert self.enable_archive_rewrite

            new_ar_path = self.workdir / "NEW_FUCKING_ARCHIVE.pkg"
            logging.info(f"Rebuilding PyInstaller archive: {new_ar_path}")

            writer = ArchiveWriter(new_ar_path)
            with writer:
                # For each entry in the original archive TOC...
                for toc_entry in self.pyi_ar.toc:
                    # Was this rewritten?
                    if toc_entry.name in rewritten_libs:
                        # Add from modified file
                        logging.debug(f"  Copying {toc_entry.name} from modified lib!")
                        modified_lib_path = self.workdir / toc_entry.name
                        data = modified_lib_path.read_bytes()

                        writer.write_blob(
                            name=toc_entry.name,
                            typecode=toc_entry.typecode,
                            data=data,
                            compress=True,  # TODO ???
                        )
                    else:
                        # Copy from input archive
                        logging.debug(
                            f"  Copying {toc_entry.name} from original archive"
                        )
                        raw_data = self.pyi_ar.extract_raw(toc_entry)
                        # raw_data may or may not be compressed

                        # TODO: Add ArchiveWriter.copy_from(other_ar, toc_entry)?
                        writer.write_raw(
                            name=toc_entry.name,
                            typecode=toc_entry.typecode,
                            data=raw_data,
                            compression_flag=toc_entry.compression_flag,
                            uncompressed_length=toc_entry.uncompressed_length,
                        )

                writer.finalize(
                    pyvers=self.pyi_ar.cookie.pyvers,
                    pylib_name=self.pyi_ar.cookie.pylib_name,
                )

            logging.info(f"Wrote new PyInstaller archive: {new_ar_path}")

            # Replace the original archive in the user program PyInstaller app

            # XXX Figure out why this causes corruption (test/pyinstall-lib-runpath)
            #
            # At build time:
            # objcopy: /tmp/sttlniT3: warning: allocated section `.dynsym' not in segment
            #
            # At runtime: segfault
            #
            # GDB:
            # warning: Loadable section ".dynamic" outside of ELF segments
            # warning: Loadable section ".dynsym" outside of ELF segments
            # warning: Loadable section ".dynstr" outside of ELF segments
            #
            # elf_update_section(self.sx.tmpprog, _ARCHIVE_ELF_SECTION_NAME, new_ar_path)
            #
            # elf_remove_section(self.sx.tmpprog, _ARCHIVE_ELF_SECTION_NAME)
            # elf_add_section(self.sx.tmpprog, _ARCHIVE_ELF_SECTION_NAME, new_ar_path)

            new_ar_data = new_ar_path.read_bytes()

            assert self.sx.tmpprog
            with ELFFileX.open(self.sx.tmpprog) as elf:
                pydata_sec = elf.get_section_by_name(_ARCHIVE_ELF_SECTION_NAME)
                assert pydata_sec
                logging.info(
                    f"Found {pydata_sec.name!r} section: {pydata_sec.data_size} bytes"
                    f" at offset {pydata_sec.header.sh_offset:#x}"
                )

                assert len(new_ar_data) <= pydata_sec.data_size
                target_off = pydata_sec.header.sh_offset
                extra = pydata_sec.data_size - len(new_ar_data)

            with open(self.sx.tmpprog, "r+b") as f:
                f.seek(target_off)
                f.write(new_ar_data)
                f.write(b"Z" * extra)
            logging.info(f"Patched {self.sx.tmpprog}")

    def _extract_binaries(self) -> list[Path]:
        result = []

        for toc_entry in self.pyi_ar.toc:
            # Only process binary files
            # See xformdict in PyInstaller.building.api.PKG
            if toc_entry.typecode != "b":
                continue

            # Extract it to a temporary location
            data = self.pyi_ar.extract(toc_entry)
            tmppath = self.workdir / toc_entry.name
            logging.debug(f"Extracting to {tmppath}")
            mkdirs_for(tmppath)
            tmppath.write_bytes(data)

            # Silence "you do not have execution permission" warning from ldd
            make_executable(tmppath)

            # We can't use yield here, because we need all of the libraries to be
            # extracted prior to running ldd (see #61)
            result.append(tmppath)

        return result

    def _audit_libs(self, libs: Iterable[Path]) -> set[str]:
        """Audit the dynamic libraries included in the PyInstaller archive

        Returns a set of modified library names (as found in the TOC).
        """
        rewritten: set[str] = set()
        errors = []
        for libpath in libs:
            libname = str(libpath.relative_to(self.workdir))

            # Check for RPATH/RUNPATH, but only "dangerous" values and let
            # "harmless" values pass (e.g. "$ORIGIN/cffi.libs")
            try:
                self.sx.check_library_rpath(str(libpath), dangerous_only=True)
            except (UnsupportedRpathError, UnsupportedRunpathError) as e:
                if self.enable_archive_rewrite:
                    # Experimental new behavior: Strip rpath/runpath and
                    # rewrite the PyInstaller archive.
                    logging.info(f"Removing RPATH/RUNPATH from library {libname}")
                    remove_rpath(libpath)
                    assert libname not in rewritten
                    rewritten.add(libname)
                else:
                    # Legacy beahvior: Report an error and abort.
                    errors.append(e)

        if errors:
            msg = "Unsupported PyInstaller input\n\n"
            msg += "One or more libraries included in the PyInstaller"
            msg += " archive uses unsupported RPATH/RUNPATH tags:\n\n"
            for err in errors:
                msg += f"  {err.libpath}: {err.tag}={err.value!r}\n"
            msg += "\nSee https://github.com/JonathonReinhart/staticx/issues/188"
            raise Error(msg)

        return rewritten

    def _add_required_deps(self, lib: Path) -> None:
        """Add dependencies of lib to staticx archive"""

        # Try to get any dependencies of this file
        try:
            deps = get_shobj_deps(lib, libpath=[str(self.workdir)])
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


################################################################################
# PyInstaller format


# typedef struct _archive_cookie
# {
#     char magic[8];
#     uint32_t pkg_length;
#     uint32_t toc_offset;
#     uint32_t toc_length;
#     uint32_t python_version;
#     char python_libname[64];
# } ARCHIVE_COOKIE;
#
_COOKIE_MAGIC_PATTERN = b"MEI\014\013\012\013\016"

_COOKIE_FORMAT = "!8sIIII64s"
_COOKIE_LENGTH = struct.calcsize(_COOKIE_FORMAT)


@dataclasses.dataclass(frozen=True)
class Cookie:
    archive_length: int
    toc_offset: int
    toc_length: int
    pyvers: int
    pylib_name: str

    @classmethod
    def from_bytes(cls, data: bytes) -> Cookie:
        parts = struct.unpack(_COOKIE_FORMAT, data)
        magic = parts[0]
        if magic != _COOKIE_MAGIC_PATTERN:
            raise ValueError("Invalid cookie magic")
        return cls(
            archive_length=parts[1],
            toc_offset=parts[2],
            toc_length=parts[3],
            pyvers=parts[4],
            pylib_name=parts[5].rstrip(b"\0").decode("ascii"),
        )

    def serialize(self) -> bytes:
        return struct.pack(
            _COOKIE_FORMAT,
            _COOKIE_MAGIC_PATTERN,
            self.archive_length,
            self.toc_offset,
            self.toc_length,
            self.pyvers,
            self.pylib_name.encode("ascii"),
        )


# typedef struct _toc_entry
# {
#     uint32_t entry_length;
#     uint32_t offset;
#     uint32_t length;
#     uint32_t uncompressed_length;
#     unsigned char compression_flag;
#     char typecode;
#     char name[1]; /* Variable-length name, padded to multiple of 16 */
# } TOC_ENTRY;
#
_TOC_ENTRY_FORMAT = "!IIIIBc"
_TOC_ENTRY_LENGTH = struct.calcsize(_TOC_ENTRY_FORMAT)

TocEntryStruct = struct.Struct(_TOC_ENTRY_FORMAT)


@dataclasses.dataclass(frozen=True)
class TocEntry:
    offset: int
    length: int
    uncompressed_length: int
    compression_flag: bool
    typecode: str
    name: str

    @classmethod
    def unpack_from(cls, data: bytes, offset: int = 0) -> tuple[TocEntry, int]:
        parts = TocEntryStruct.unpack_from(data, offset)

        entry_length = parts[0]
        if len(data) < offset + entry_length:
            raise ValueError("Not enough data to unpack")
        name_start = offset + TocEntryStruct.size
        name_stop = offset + entry_length
        name = data[name_start:name_stop].rstrip(b"\0").decode("utf-8")

        return cls(
            offset=parts[1],
            length=parts[2],
            uncompressed_length=parts[3],
            compression_flag=parts[4],
            typecode=parts[5].decode("ascii"),
            name=name,
        ), entry_length

    def serialize(self) -> bytes:
        name_bytes = self.name.encode("utf-8") + b"\0"

        # Pad entry to multiple of 16 bytes
        entry_length = align_up(TocEntryStruct.size + len(name_bytes), 16)

        data = (
            TocEntryStruct.pack(
                entry_length,
                self.offset,
                self.length,
                self.uncompressed_length,
                self.compression_flag,
                self.typecode.encode("ascii"),
            )
            + name_bytes
        )
        return data.ljust(entry_length, b"\0")


# See PyInstaller/builders/api.py EXE.assemble()
# Since commit 85dfef01 Use objcopy to create a vaild ELF file
# on Feb 18, 2016 first seen in v3.2.
_ARCHIVE_ELF_SECTION_NAME = "pydata"


class ArchiveWriter:
    _COMPRESSION_LEVEL = 9

    def __init__(self, outpath: Pathlike):
        self._exit_stack = contextlib.ExitStack()
        self._f = self._exit_stack.enter_context(open(outpath, "wb"))
        self._finalized = False
        self._toc_entries: list[TocEntry] = []

    def __enter__(self) -> ArchiveWriter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        if exc_type is None and not self._finalized:
            raise Exception("Not finalized!")
        return self._exit_stack.__exit__(exc_type, exc_val, exc_tb)

    def write_raw(
        self,
        name: str,
        typecode: str,
        data: bytes,
        compression_flag: bool,
        uncompressed_length: int,
    ) -> None:
        offset = self._f.tell()
        self._f.write(data)

        toc_entry = TocEntry(
            offset=offset,
            length=len(data),
            uncompressed_length=uncompressed_length,
            compression_flag=compression_flag,
            typecode=typecode,
            name=name,
        )
        self._toc_entries.append(toc_entry)

    def write_blob(
        self,
        name: str,
        typecode: str,
        data: bytes,
        compress: bool = False,
    ) -> None:
        orig_len = len(data)
        if compress:
            data = zlib.compress(data, level=self._COMPRESSION_LEVEL)
        return self.write_raw(
            name=name,
            typecode=typecode,
            data=data,
            compression_flag=compress,
            uncompressed_length=orig_len,
        )

    def finalize(
        self,
        pyvers: int,
        pylib_name: str,
    ) -> None:
        assert not self._finalized

        # Write TOC
        toc_offset = self._f.tell()
        for toc_entry in self._toc_entries:
            self._f.write(toc_entry.serialize())
        toc_length = self._f.tell() - toc_offset

        # Write Cookie
        archive_length = toc_offset + toc_length + _COOKIE_LENGTH
        cookie = Cookie(
            archive_length=archive_length,
            toc_offset=toc_offset,
            toc_length=toc_length,
            pyvers=pyvers,
            pylib_name=pylib_name,
        )
        self._f.write(cookie.serialize())
        assert self._f.tell() == archive_length

        self._finalized = True


class ArchiveReader:
    def __init__(self, raw_archive: bytes):
        self._raw_archive = raw_archive

        self.cookie = self._read_cookie()
        self.toc = self._read_toc(self.cookie)

    @classmethod
    def open_elf(cls, inpath: Pathlike) -> ArchiveReader:
        local_stack = contextlib.ExitStack()
        with local_stack:
            elf = local_stack.enter_context(ELFFileX.open(inpath))

            pydata_sec = elf.get_section_by_name(_ARCHIVE_ELF_SECTION_NAME)
            if pydata_sec is None:
                # TODO: More specific exception
                raise ValueError(f"No {_ARCHIVE_ELF_SECTION_NAME} section")

            logging.info(
                f"Found {pydata_sec.name!r} section: {pydata_sec.data_size} bytes"
                f" at offset {pydata_sec.header.sh_offset:#x}"
            )

            # TODO: To avoid lifting the entire archive into memory via .data(),
            # we can access the underlying stream directly:
            # * Change __init__ to accept a stream.
            # * Implement a constrained stream view wrapper for just the archive range.
            # * Use ExitStack.pop_all() to "move" the file into the class.
            # * Requires 'assert not pydata_sec.compressed'

            raw_archive = pydata_sec.data()
            return cls(raw_archive)

    def __enter__(self) -> ArchiveReader:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool | None:
        return None

    def _read_cookie(self) -> Cookie:
        # Read cookie from end
        # TODO: Handle ValueError for invalid cookie
        cookie = Cookie.from_bytes(self._raw_archive[-_COOKIE_LENGTH:])
        logging.debug(f"Cookie: {cookie}")

        # Sanity checks
        # Ensure archive wholly occupies pydata section.
        assert cookie.archive_length == len(self._raw_archive)
        # Ensure TOC is within archive
        assert cookie.toc_offset < cookie.archive_length
        # Ensure TOC + Cookie are at end of archive
        assert (
            cookie.toc_offset + cookie.toc_length + _COOKIE_LENGTH
            == cookie.archive_length
        )
        # Ensure pyvers is Python 3.x
        assert 300 < cookie.pyvers < 400
        # Ensure python lib name looks reasonable
        assert cookie.pylib_name.startswith("libpython3.")

        return cookie

    def _read_toc(self, cookie: Cookie) -> list[TocEntry]:
        raw_toc = self._raw_archive[
            cookie.toc_offset : cookie.toc_offset + cookie.toc_length
        ]

        cursor = 0
        result = []
        while cursor < len(raw_toc):
            entry, entry_length = TocEntry.unpack_from(raw_toc, cursor)
            cursor += entry_length
            result.append(entry)
        return result

    def extract_raw(self, entry: TocEntry) -> bytes:
        return self._raw_archive[entry.offset : entry.offset + entry.length]

    def extract(self, entry: TocEntry) -> bytes:
        data = self.extract_raw(entry)
        if entry.compression_flag:
            data = zlib.decompress(data)
        return data


################################################################################
# Test main


def _cmd_extract(args: argparse.Namespace) -> None:
    reader = ArchiveReader.open_elf(args.archive)
    with reader:
        for toc_entry in reader.toc:
            data = reader.extract(toc_entry)
            outpath = args.outdir / toc_entry.name
            mkdirs_for(outpath)
            with open(outpath, "wb") as f:
                f.write(data)
            logging.info(f"Wrote {toc_entry.name}")


def _cmd_recreate(args: argparse.Namespace) -> None:
    reader = ArchiveReader.open_elf(args.input)
    writer = ArchiveWriter(args.output)

    with reader, writer:
        for toc_entry in reader.toc:
            raw_data = reader.extract_raw(toc_entry)
            # raw_data may or may not be compressed

            writer.write_raw(
                name=toc_entry.name,
                typecode=toc_entry.typecode,
                data=raw_data,
                compression_flag=toc_entry.compression_flag,
                uncompressed_length=toc_entry.uncompressed_length,
            )

        writer.finalize(
            pyvers=reader.cookie.pyvers,
            pylib_name=reader.cookie.pylib_name,
        )

    logging.info(f"New archive written to {args.output}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        title="subcommands",
        dest="command",
        required=True,
    )

    extract_parser = subparsers.add_parser(
        "extract",
        help="Extracts an input archive",
    )
    extract_parser.set_defaults(func=_cmd_extract)
    extract_parser.add_argument("archive", type=Path)
    extract_parser.add_argument("outdir", type=Path)

    recreate_parser = subparsers.add_parser(
        "recreate",
        help="Recreate an input archive",
    )
    recreate_parser.set_defaults(func=_cmd_recreate)
    recreate_parser.add_argument("input", type=Path)
    recreate_parser.add_argument("output", type=Path)

    return parser.parse_args()


def _main() -> None:
    args = _parse_args()
    logging.basicConfig(level=logging.DEBUG)

    args.func(args)


if __name__ == "__main__":
    _main()
