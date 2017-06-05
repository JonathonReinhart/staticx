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
import errno
from itertools import chain

from .errors import *
from .utils import *

ARCHIVE_SECTION = ".staticx.archive"
INTERP_FILENAME = ".staticx.interp"
PROG_FILENAME   = ".staticx.prog"

MAX_INTERP_LEN = 256
MAX_RPATH_LEN = 256

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

# locates a library based on the provided base file name.  uses ldconfig -p to accomplish this.  if the file 
#   is not found, the starting base name is returned. 
def locateLibrary(libbasename):
    try:
        output = subprocess.check_output(['ldconfig','-p'])
    except subprocess.CalledProcessError as e:
        raise ToolError('ldconfig')
    
    pat = re.compile('\s*{}.* => (.+)'.format(libbasename))
    for line in output.decode('ascii').splitlines():
        m = pat.match(line)
        if m:
            return m.group(1)

    return libbasename

# checks the file at the location provided for an indication that it is a pyinstaller created exe.  
#   Pyinstaller created executables have additional library requirements (libpthread, libm)
def is_pyinstall_exe (path):
    # use readelf -SW to list the section headers. Searching the results in reverse since the section we want
    #   is usually near the end of the list of headers.
    for line in reversed(readelf(path,'-S','-W')):
        if line.find('pydata') != -1:
            return True

    return False

# Adds pyinstaller required libs if they're not already in the list.  if the list is empty, a new one is 
#   created.
def add_pyinstall_libs(liblist):
    if liblist is None:
        liblist = []

    pyi_libs = ['libpthread.so.0', 'libm.so.6']

    for curlib in liblist:
        bn = os.path.basename(curlib)
        if bn in pyi_libs:
            pyi_libs.remove(bn)

    for lib in pyi_libs:
        liblist.append(locateLibrary(lib))

    return liblist



def get_symlink_target(path):
    dirpath = os.path.dirname(os.path.abspath(path))
    return os.path.join(dirpath, os.readlink(path))

def make_symlink_TarInfo(name, target):
    t = tarfile.TarInfo()
    t.type = tarfile.SYMTYPE
    t.name = name
    t.linkname = target
    return t


def generate_archive(prog, interp, extra_libs=None):
    logging.info("Program interpreter: " + interp)

    if extra_libs is None:
        extra_libs = []

    f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')
    with tarfile.open(fileobj=f, mode='w') as tar:

        # Add the program
        arcname = PROG_FILENAME
        logging.info("Adding {} as {}".format(prog, arcname))
        tar.add(prog, arcname=arcname)

        # Add all of the libraries
        for lib in chain(get_shobj_deps(prog), extra_libs):
            if lib.startswith('linux-vdso.so'):
                continue

            # using a temp library name to walk the link list, mainly to preserve the original name for later.
            linklib = lib

            # 'recursively' step through any symbolic links, generating local links inside the archive
            while os.path.islink(linklib):
                arcname = os.path.basename(linklib)
                linklib = get_symlink_target(linklib)
                logging.info("    Adding Symlink {} => {}".format(arcname, os.path.basename(linklib)))
                # add a symlink.  at this point the target probably doesn't exist, but that doesn't matter yet
                tar.addfile(make_symlink_TarInfo(arcname, os.path.basename(linklib)))

            # left with a real file at this point, add it to the archive.
            arcname = os.path.basename(linklib)
            logging.info("    Adding {} as {}".format(linklib, arcname))
            tar.add(linklib, arcname=arcname)

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

<<<<<<< HEAD
=======
    # Check for pyinstaller exe, adding additional libs typically required for pyinstalled apps that don't
    #   normally get pulled in (friends of libc, for instance)
    #   More robust solution may be to perform a deep scan of internal library depencencies
    if is_pyinstall_exe(prog):
        libs = add_pyinstall_libs(libs)

    # set tmpoutput to None, so as not to confuse python during an error where the output dir isn't set
    tmpoutput = None

>>>>>>> d4c7706... Examine input app for signs of pyinstaller -- auto add libs
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
