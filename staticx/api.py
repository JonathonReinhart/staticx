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
from .constants import *
from .hooks import run_hooks

def generate_archive(orig_prog, copied_prog, interp, tmpdir, extra_libs=None, strip=False, compress=True):
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
            ar.add_library(libpath)

        run_hooks(ar, orig_prog)

    f.flush()
    return f

def _locate_bootloader(debug=False):
    """Determine path to bootloader"""
    pkg_path = os.path.dirname(__file__)
    blname = 'bootloader-debug' if debug else 'bootloader'
    blpath = os.path.abspath(os.path.join(pkg_path, blname))
    if not os.path.isfile(blpath):
        raise InternalError("bootloader not found at {}".format(blpath))
    return blpath


def _check_bootloader_compat(bootloader, prog):
    """Verify the bootloader machine matches that of the user program"""
    bldr_mach = get_machine(bootloader)
    prog_mach = get_machine(prog)
    if bldr_mach != prog_mach:
        raise FormatMismatchError("Bootloader machine ({}) doesn't match "
                "program machine ({})".format(bldr_mach, prog_mach))


def _copy_to_tempfile(srcpath, **kwargs):
    fdst = NamedTemporaryFile(**kwargs)
    with open(srcpath, 'rb') as fsrc:
        shutil.copyfileobj(fsrc, fdst)

    fdst.flush()
    shutil.copystat(srcpath, fdst.name)
    return fdst


def generate(prog, output, libs=None, strip=False, compress=True, debug=False):
    """Main API: Generate a staticx executable

    Parameters:
    prog:   Dynamic executable to staticx
    output: Path to result
    libs: Extra libraries to include
    strip: Strip binaries to reduce size
    debug: Run in debug mode (use debug bootloader)
    """
    bootloader = _locate_bootloader(debug)
    _check_bootloader_compat(bootloader, prog)


    tmpdir = mkdtemp(prefix='staticx-archive-')

    # First, learn things about the original program
    orig_interp = get_prog_interp(prog)

    # Now modify a copy of the user prog
    tmpprog = _copy_to_tempfile(prog, prefix='staticx-prog-', delete=False).name
    tmpoutput = None
    try:
        # Strip user prog before modifying it
        if strip:
            logging.info("Stripping prog {}".format(tmpprog))
            strip_elf(tmpprog)

        # Set long dummy INTERP and RPATH in the executable to allow plenty of space
        # for bootloader to patch them at runtime, without the reording complexity
        # that patchelf has to do.
        new_interp = 'i' * MAX_INTERP_LEN
        new_rpath = 'r' * MAX_RPATH_LEN
        patch_elf(tmpprog, interpreter=new_interp, rpath=new_rpath, force_rpath=True)

        # Work on a temp copy of the bootloader
        tmpoutput = _copy_to_tempfile(bootloader, prefix='staticx-output-', delete=False).name

        if strip:
            logging.info("Stripping bootloader {}".format(tmpoutput))
            strip_elf(tmpoutput)

        # Starting from the bootloader, append archive
        with generate_archive(prog, tmpprog, orig_interp, tmpdir, libs, strip=strip, compress=compress) as ar:
            elf_add_section(tmpoutput, ARCHIVE_SECTION, ar.name)

        # Move the temporary output file to its final place
        move_file(tmpoutput, output)
        tmpoutput = None

    finally:
        os.remove(tmpprog)
        shutil.rmtree(tmpdir)

        if tmpoutput:
            os.remove(tmpoutput)
