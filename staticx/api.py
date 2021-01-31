# StaticX
# Copyright 2017 Jonathon Reinhart
# https://github.com/JonathonReinhart/staticx
#
import shutil
from tempfile import NamedTemporaryFile, mkdtemp
import os
from os.path import basename
import logging
from itertools import chain

from .errors import *
from .utils import *
from .elf import *
from .archive import SxArchive
from .assets import copy_asset_to_tempfile
from .constants import *
from .hooks import run_hooks

def generate_archive(orig_prog, copied_prog, interp, tmpdir, extra_libs=None, strip=False, compress=True, debug=False):
    """ Generate a StaticX archive

    Args:
        orig_prog: Path to original user program
        copied_prog: Path to user program which has been prepped
        interp: Original program interpreter
        tmpdir: Temporary directory to use for stripping libraries
        extra_libs: Additional libraries to add to the archive
        strip: Whether or not to strip libraries
        compress: Whether or not to create a compressed archive

    Returns:
        A handle to the created file object
    """
    logging.info("Program interpreter: " + interp)

    if extra_libs is None:
        extra_libs = []

    f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')
    with SxArchive(fileobj=f, mode='w', compress=compress) as ar:
        run_hooks(
                archive = ar,
                orig_prog = orig_prog,
                copied_prog = copied_prog,
                debug = debug,
                )

        # Make the program depend on all of the libraries added by hooks.
        # This will ensure they those libaries are loaded, even in light
        # of any RUNPATH on nested libs.
        patch_elf(copied_prog, add_needed=ar.libraries)

        ar.add_program(copied_prog, basename(orig_prog))
        ar.add_interp_symlink(interp)

        # Add all of the libraries
        for libpath in chain(get_shobj_deps(orig_prog), extra_libs):
            if strip:
                # Copy the library to the temp dir before stripping
                tmplib = os.path.join(tmpdir, basename(libpath))
                logging.info("Copying {} to {}".format(libpath, tmplib))
                shutil.copy(libpath, tmplib)

                # Strip the library
                logging.info("Stripping binary {}".format(tmplib))
                strip_elf(tmplib)

                libpath = tmplib

            # Add the library to the archive
            ar.add_library(libpath, exist_ok=True)


    f.flush()
    return f


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


def generate(prog, output, libs=None, strip=False, compress=True, debug=False):
    """Main API: Generate a staticx executable

    Parameters:
    prog:   Dynamic executable to staticx
    output: Path to result
    libs: Extra libraries to include
    strip: Strip binaries to reduce size
    debug: Run in debug mode (use debug bootloader)
    """

    tmpoutput = None
    tmpprog = None
    tmpdir = None

    # Work on a temp copy of the bootloader which becomes the output program
    tmpoutput = _get_bootloader(debug)

    try:
        _check_bootloader_compat(tmpoutput, prog)

        # First, learn things about the original program
        orig_interp = get_prog_interp(prog)

        # Now modify a copy of the user prog
        tmpprog = copy_to_tempfile(prog, prefix='staticx-prog-', delete=False).name

        # Strip user prog before modifying it
        if strip:
            logging.info("Stripping prog {}".format(tmpprog))
            strip_elf(tmpprog)

        # Set long dummy INTERP and RPATH in the executable to allow plenty of space
        # for bootloader to patch them at runtime, without the reording complexity
        # that patchelf has to do.
        new_interp = 'i' * MAX_INTERP_LEN
        new_rpath = 'r' * MAX_RPATH_LEN
        patch_elf(tmpprog, interpreter=new_interp, rpath=new_rpath,
                  force_rpath=True, no_default_lib=True)

        if strip:
            logging.info("Stripping bootloader {}".format(tmpoutput))
            strip_elf(tmpoutput)

        # Starting from the bootloader, append archive
        tmpdir = mkdtemp(prefix='staticx-archive-')
        with generate_archive(prog, tmpprog, orig_interp, tmpdir, libs,
                strip=strip, compress=compress, debug=debug) as ar:
            elf_add_section(tmpoutput, ARCHIVE_SECTION, ar.name)

        # Move the temporary output file to its final place
        move_file(tmpoutput, output)
        tmpoutput = None

    finally:
        if tmpprog:
            os.remove(tmpprog)

        if tmpdir:
            shutil.rmtree(tmpdir)

        if tmpoutput:
            os.remove(tmpoutput)
