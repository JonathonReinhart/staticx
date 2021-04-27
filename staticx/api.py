# StaticX
# Copyright 2017 Jonathon Reinhart
# https://github.com/JonathonReinhart/staticx
#
import shutil
from tempfile import NamedTemporaryFile, mkdtemp
import os
from os.path import basename
import logging

from .errors import *
from .utils import *
from .elf import *
from .archive import SxArchive
from .assets import copy_asset_to_tempfile
from .constants import *
from .hooks import run_hooks




def _get_bootloader(debug=False):
    """Get a temporary copy of the bootloader"""
    fbl = copy_asset_to_tempfile('bootloader', debug, prefix='staticx-output-', delete=False)
    make_executable(fbl.name)
    return fbl.name


def _check_bootloader_compat(bootloader, prog):
    """Verify the bootloader machine matches that of the user program"""
    bldr_mach = get_machine(bootloader)
    prog_mach = get_machine(prog)
    if bldr_mach != prog_mach:
        raise FormatMismatchError("Bootloader machine ({}) doesn't match "
                "program machine ({})".format(bldr_mach, prog_mach))

class StaticxGenerator:
    """StaticxGenerator is responsible for producing a staticx-ified executable.
    """

    def __init__(self, prog, strip=False, compress=True, debug=False, cleanup=True):
        """
        Parameters:
        prog:   Dynamic executable to staticx
        debug:  Run in debug mode (use debug bootloader)
        """
        self.orig_prog = prog
        self.strip = strip
        self.compress = compress
        self.debug = debug
        self.cleanup = cleanup

        self._generate_called = False

        self.tmpoutput = None
        self.tmpprog = None
        self.tmpdir = None

        f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')
        self.sxar = SxArchive(fileobj=f, mode='w', compress=self.compress)


    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        if self.cleanup:
            self._cleanup()

    def _cleanup(self):
        if self.tmpoutput:
            os.remove(self.tmpoutput)
            self.tmpoutput = None

        if self.tmpprog:
            os.remove(self.tmpprog)
            self.tmpprog = None

        if self.tmpdir:
            shutil.rmtree(self.tmpdir)
            self.tmpdir = None

        if self.sxar:
            self.sxar.close()
            self.sxar = None



    def generate(self, output):
        """Generate a Staticx program

        Parameters:
        output: Path where output file is written
        """
        # Only allow generate() to be called once per instance.
        # In the future we might relax this, but YAGNI for now.
        if self._generate_called:
            raise InternalError("generate() already called")
        self._generate_called = True

        # Work on a temp copy of the bootloader which becomes the output program
        self.tmpoutput = _get_bootloader(self.debug)

        _check_bootloader_compat(self.tmpoutput, self.orig_prog)

        # First, learn things about the original program
        orig_interp = get_prog_interp(self.orig_prog)
        logging.info("Program interpreter: " + orig_interp)

        # Now modify a copy of the user prog
        self.tmpprog = copy_to_tempfile(self.orig_prog, prefix='staticx-prog-', delete=False).name
        self._fixup_prog()

        if self.strip:
            # TODO: Now that we have ship separate debug/release bootloaders
            # do we ever want and need to do this at staticx-time?
            logging.info("Stripping bootloader {}".format(self.tmpoutput))
            strip_elf(self.tmpoutput)


        # Build the archive to be appended
        self.tmpdir = mkdtemp(prefix='staticx-archive-')
        with self.sxar as ar:
            run_hooks(self)

            ar.add_program(self.tmpprog, basename(self.orig_prog))
            ar.add_interp_symlink(orig_interp)

            # Add all of the libraries
            for libpath in get_shobj_deps(self.orig_prog):
                self.add_library(libpath, exist_ok=True)

        # errr...
        arf = self.sxar.fileobj
        arf.flush()

        # Starting from the bootloader, append archive
        elf_add_section(self.tmpoutput, ARCHIVE_SECTION, arf.name)

        # Move the temporary output file to its final place
        move_file(self.tmpoutput, output)
        self.tmpoutput = None


    def add_library(self, libpath, exist_ok=False):
        libname = basename(libpath)
        if libname in self.sxar.libraries:
            if exist_ok:
                return
            raise LibExistsError(libname)

        # Copy the library to the temp dir before stripping
        tmplib = os.path.join(self.tmpdir, basename(libpath))
        logging.info("Copying {} to {}".format(libpath, tmplib))
        shutil.copy(libpath, tmplib)

        if self.strip:
            # Strip the library
            logging.info("Stripping binary {}".format(tmplib))
            strip_elf(tmplib)

            libpath = tmplib

        # Add the library to the archive
        self.sxar.add_library(libpath, exist_ok=True)


    def _fixup_prog(self):
        """Fixup our temporary copy of the user's program"""

        # Strip user prog before modifying it
        if self.strip:
            logging.info("Stripping prog {}".format(self.tmpprog))
            strip_elf(self.tmpprog)

        # Set long dummy INTERP and RPATH in the executable to allow plenty of space
        # for bootloader to patch them at runtime, without the reording complexity
        # that patchelf has to do.
        new_interp = 'i' * MAX_INTERP_LEN
        new_rpath = 'r' * MAX_RPATH_LEN
        patch_elf(self.tmpprog, interpreter=new_interp, rpath=new_rpath,
                  force_rpath=True, no_default_lib=True)


def generate(prog, output, libs=None, strip=False, compress=True, debug=False):
    """Main API: Generate a staticx executable

    Parameters:
    prog:   Dynamic executable to staticx
    output: Path to result
    libs: Extra libraries to include
    strip: Strip binaries to reduce size
    debug: Run in debug mode (use debug bootloader)
    """
    gen = StaticxGenerator(
            prog=prog,
            strip=strip,
            compress=compress,
            debug=debug,
            )
    with gen:
        for lib in (libs or []):
            gen.add_library(lib)

        gen.generate(output=output)
