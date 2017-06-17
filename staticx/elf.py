import subprocess
import re
import logging
import errno

from .errors import *

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
