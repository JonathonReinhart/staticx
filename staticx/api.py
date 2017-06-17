# StaticX
# Copyright 2017 Jonathon Reinhart
# https://github.com/JonathonReinhart/staticx
#
import shutil
from tempfile import NamedTemporaryFile
import os
import logging
from itertools import chain

from .errors import *
from .utils import *
from .elf import *
from .archive import SxArchive
from .constants import *
from .hooks import run_hooks

def generate_archive(prog, interp, extra_libs=None):
    logging.info("Program interpreter: " + interp)

    if extra_libs is None:
        extra_libs = []

    f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')
    with SxArchive(fileobj=f, mode='w') as ar:

        ar.add_program(prog)
        ar.add_interp_symlink(interp)

        # Add all of the libraries
        for libpath in chain(get_shobj_deps(prog), extra_libs):
            ar.add_library(libpath)

        run_hooks(ar, prog)

    f.flush()
    return f

def _locate_bootloader():
    """Determine path to bootloader"""
    pkg_path = os.path.dirname(__file__)
    blpath = os.path.abspath(os.path.join(pkg_path, 'bootloader'))
    if not os.path.isfile(blpath):
        raise InternalError("bootloader not found at {}".format(blpath))
    return blpath

def _copy_to_tempfile(srcpath, **kwargs):
    fdst = NamedTemporaryFile(**kwargs)
    with open(srcpath, 'rb') as fsrc:
        shutil.copyfileobj(fsrc, fdst)

    fdst.flush()
    shutil.copystat(srcpath, fdst.name)
    return fdst


def generate(prog, output, libs=None, bootloader=None):
    """Main API: Generate a staticx executable

    Parameters:
    prog:   Dynamic executable to staticx
    output: Path to result
    bootloader: Override the bootloader binary
    """
    if not bootloader:
        bootloader = _locate_bootloader()

    # First, learn things about the original program
    orig_interp = get_prog_interp(prog)

    # Now modify a copy of the user prog
    tmpprog = _copy_to_tempfile(prog, prefix='staticx-prog-', delete=False).name
    tmpoutput = None
    try:
        # Set long dummy INTERP and RPATH in the executable to allow plenty of space
        # for bootloader to patch them at runtime, without the reording complexity
        # that patchelf has to do.
        new_interp = 'i' * MAX_INTERP_LEN
        new_rpath = 'r' * MAX_RPATH_LEN
        patch_elf(tmpprog, interpreter=new_interp, rpath=new_rpath, force_rpath=True)

        # Work on a temp copy of the bootloader
        tmpoutput = _copy_to_tempfile(bootloader, prefix='staticx-output-', delete=False).name

        # Starting from the bootloader, append archive
        with generate_archive(tmpprog, orig_interp, libs) as ar:
            elf_add_section(tmpoutput, ARCHIVE_SECTION, ar.name)

        # Move the temporary output file to its final place
        shutil.move(tmpoutput, output)
        tmpoutput = None

    finally:
        os.remove(tmpprog)

        if tmpoutput:
            os.remove(tmpoutput)
