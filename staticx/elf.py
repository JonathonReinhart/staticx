import subprocess
import sys
import re
import logging
import errno

from .errors import *

class ExternTool(object):
    def __init__(self, cmd, os_pkg, stderr_ignore=[], encoding='utf-8'):
        self.cmd = cmd
        self.os_pkg = os_pkg
        self.capture_stdout = True
        self.stderr_ignore = stderr_ignore
        self.encoding = encoding

    def __should_ignore(self, line):
        for ignore in self.stderr_ignore:
            if ignore in line:
                return True
        return False

    def run(self, *args):
        args = list(args)
        args.insert(0, self.cmd)

        kw = dict(stderr=subprocess.PIPE)
        if self.capture_stdout:
            kw['stdout'] = subprocess.PIPE

        logging.debug("Running " + str(args))
        try:
            p = subprocess.Popen(args, **kw)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise MissingToolError(self.cmd, self.os_pkg)
            raise

        stdout, stderr = p.communicate()
        stdout = stdout.decode(self.encoding)
        stderr = stderr.decode(self.encoding)

        # Hide ignored lines from stderr
        for line in stderr.splitlines(True):
            if self.__should_ignore(line):
                continue
            sys.stderr.write(line)

        if p.returncode != 0:
            raise ToolError(self.cmd, '{} returned {}'.format(self.cmd, p.returncode))

        return stdout




tool_ldd        = ExternTool('ldd', 'binutils')
tool_readelf    = ExternTool('readelf', 'binutils')
tool_objcopy    = ExternTool('objcopy', 'binutils')
tool_patchelf   = ExternTool('patchelf', 'patchelf',
                    stderr_ignore = [
                        'working around a Linux kernel bug by creating a hole',
                    ])
tool_strip      = ExternTool('strip', 'binutils')

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

    for line in output.splitlines():
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
    return output.splitlines()

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

def strip_elf(path):
    tool_strip.run(path)
