# StaticX
# Copyright 2017 Jonathon Reinhart
# https://github.com/JonathonReinhart/staticx
#
import subprocess
import shutil
from tempfile import NamedTemporaryFile, mkdtemp
import os
import re
import logging
import errno
from itertools import chain

from .errors import *
from .utils import *
from .archive import SxArchive
from .constants import *


class ExternTool(object):
    def __init__(self, cmd, os_pkg):
        self.cmd = cmd
        self.os_pkg = os_pkg

    def run(self, *args):
        args = list(args)
        args.insert(0, self.cmd)
        try:
            logging.debug("Running " + str(args))
            return subprocess.check_output(args)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise MissingToolError(self.cmd, self.os_pkg)
            raise
        except subprocess.CalledProcessError as e:
            raise ToolError(self.cmd)

tool_ldd        = ExternTool('ldd', 'binutils')
tool_readelf    = ExternTool('readelf', 'binutils')
tool_objcopy    = ExternTool('objcopy', 'binutils')
tool_patchelf   = ExternTool('patchelf', 'patchelf')

def get_shobj_deps(path):
    output = tool_ldd.run(path)

    # Example:
    #	libc.so.6 => /usr/lib64/libc.so.6 (0x00007f42ac010000)
    #	/lib64/ld-linux-x86-64.so.2 (0x0000557376e75000)
    pat = re.compile('\t([\w./+-]*) (?:=> ([\w./+-]*) )?\((0x[0-9a-fA-F]*)\)')

    ignore_list = 'linux-vdso.so'

    def ignore(p):
        for name in ignore_list:
            if libpath.startswith(name):
                return True
        return False

    for line in output.decode('ascii').splitlines():
        m = pat.match(line)
        if not m:
            raise ToolError('ldd', "Unexpected line in ldd output: " + line)
        libname  = m.group(1)
        libpath  = m.group(2)
        baseaddr = int(m.group(3), 16)

        libpath = libpath or libname

        if ignore(libpath):
            continue
        yield libpath


def readelf(path, *args):
    args = list(args)
    args.append(path)
    output = tool_readelf.run(*args)
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
    tool_objcopy.run(
        '--add-section', '{}={}'.format(secname, secfilename),
        elfpath)

def patch_elf(path, interpreter=None, rpath=None, force_rpath=False):
    args = []
    if interpreter:
        args += ['--set-interpreter', interpreter]
    if rpath:
        args += ['--set-rpath', rpath]
    if force_rpath:
        args.append('--force-rpath')
    args.append(path)

    tool_patchelf.run(*args)


def process_pyinstaller_archive(ar, prog):
    # See utils/cliutils/archive_viewer.py

    # If PyInstaller is not installed, do nothing
    try:
        from PyInstaller.archive.readers import CArchiveReader, NotAnArchiveError
    except ImportError:
        return

    # Attempt to open the program as PyInstaller archive
    try:
        pyi_ar = CArchiveReader(prog)
    except:
        # Silence all PyInstaller exceptions here
        return
    logging.info("Opened PyInstaller archive!")

    # Create a temporary directory
    # TODO PY3: Use tempfile.TemporaryDirectory and cleanup()
    tmpdir = mkdtemp(prefix='staticx-pyi-')

    try:
        # Process the archive, looking at all shared libs
        for n, item in enumerate(pyi_ar.toc.data):
            (dpos, dlen, ulen, flag, typcd, name) = item

            # Only process binary files
            # See xformdict in PyInstaller.building.api.PKG
            if typcd != 'b':
                continue

            # Extract it to a temporary location
            x, data = pyi_ar.extract(n)
            tmppath = os.path.join(tmpdir, name)
            logging.debug("Extracting to {}".format(tmppath))
            with open(tmppath, 'wb') as f:
                f.write(data)

            # Silence "you do not have execution permission" warning from ldd
            make_executable(tmppath)

            # Add any missing libraries to our archive
            for libpath in get_shobj_deps(tmppath):
                lib = os.path.basename(libpath)

                if lib in ar.libraries:
                    logging.debug("{} already in staticx archive".format(lib))
                    continue

                if pyi_ar.toc.find(lib) != -1:
                    logging.debug("{} already in pyinstaller archive".format(lib))
                    continue

                ar.add_library(libpath)
    finally:
        shutil.rmtree(tmpdir)


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


        process_pyinstaller_archive(ar, prog)

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
