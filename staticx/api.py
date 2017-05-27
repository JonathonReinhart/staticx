# StaticX
# Copyright 2017 Jonathon Reinhart
# https://github.com/JonathonReinhart/staticx
#
import subprocess
import tarfile
import shutil
from tempfile import NamedTemporaryFile
import os
import re
import logging

from .errors import *

__version__ = '0.0.1'

ARCHIVE_SECTION = ".staticx.archive"
INTERP_FILENAME = ".staticx.interp"
PROG_FILENAME   = ".staticx.prog"

def get_shobj_deps(path):
    try:
        output = subprocess.check_output(['ldd', path])
    except FileNotFoundError:
        raise MissingToolError('ldd', 'binutils')
    except subprocess.CalledProcessError as e:
        raise ToolError('ldd')

    # Example:
    #	libc.so.6 => /usr/lib64/libc.so.6 (0x00007f42ac010000)
    #	/lib64/ld-linux-x86-64.so.2 (0x0000557376e75000)
    pat = re.compile('\t([\w./+-]*) (?:=> ([\w./+-]*) )?\((0x[0-9a-fA-F]*)\)')

    for line in output.decode('ascii').splitlines():
        m = pat.match(line)
        if not m:
            raise ToolError('ldd', "Unexpected line in ldd output: " + line)
        libname  = m.group(1)
        libpath  = m.group(2)
        baseaddr = int(m.group(3), 16)

        libpath = libpath or libname
        yield libpath


def readelf(path, *args):
    args = ['readelf'] + list(args) + [path]
    try:
        output = subprocess.check_output(args)
    except FileNotFoundError:
        raise MissingToolError('readelf', 'binutils')
    except subprocess.CalledProcessError as e:
        raise ToolError('readelf')
    return output.decode('ascii').splitlines()

def get_prog_interp(path):
    # Example:
    #      [Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
    pat = re.compile('\s*\[Requesting program interpreter: ([\w./-]+)\]')
    for line in readelf(path, '-l', '-W'):
        m = pat.match(line)
        if m:
            return m.group(1)
    raise InvalidInputError("{}: not a dynamic executable".format(path))

def elf_add_section(elfpath, secname, secfilename):
    subprocess.check_call(['objcopy',
        '--add-section', '{}={}'.format(secname, secfilename),
        elfpath])


def get_symlink_target(path):
    dirpath = os.path.dirname(os.path.abspath(path))
    return os.path.join(dirpath, os.readlink(path))

def make_symlink_TarInfo(name, target):
    t = tarfile.TarInfo()
    t.type = tarfile.SYMTYPE
    t.name = name
    t.linkname = target
    return t


def generate_archive(prog):
    interp = get_prog_interp(prog)
    logging.info("Program interpreter: " + interp)

    f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')
    with tarfile.open(fileobj=f, mode='w') as tar:

        # Add the program
        arcname = PROG_FILENAME
        logging.info("Adding {} as {}".format(prog, arcname))
        tar.add(prog, arcname=arcname)

        # Add all of the libraries
        for lib in get_shobj_deps(prog):
            if lib.startswith('linux-vdso.so'):
                continue

            arcname = os.path.basename(lib)
            logging.info("    Adding {} as {}".format(lib, arcname))
            tar.add(lib, arcname=arcname)

            if os.path.islink(lib):
                reallib = get_symlink_target(lib)
                arcname = os.path.basename(reallib)
                logging.info("    Adding {} as {}".format(reallib, arcname))
                tar.add(reallib, arcname=arcname)
                # TODO: Recursively handle symlinks

            # Add special symlink for interpreter
            if lib == interp:
                tar.addfile(make_symlink_TarInfo(INTERP_FILENAME, os.path.basename(lib)))

    f.flush()
    return f

def _locate_bootloader():
    """Determine path to bootloader"""
    pkg_path = os.path.dirname(__file__)
    blpath = os.path.abspath(os.path.join(pkg_path, 'bootloader'))
    if not os.path.isfile(blpath):
        raise InternalError("bootloader not found at {}".format(blpath))
    return blpath


def generate(prog, output, bootloader=None):
    """Main API: Generate a staticx executable

    Parameters:
    prog:   Dynamic executable to staticx
    output: Path to result
    bootloader: Override the bootloader binary
    """
    if not bootloader:
        bootloader = _locate_bootloader()

    shutil.copy2(bootloader, output)

    with generate_archive(prog) as ar:
        elf_add_section(output, ARCHIVE_SECTION, ar.name)
