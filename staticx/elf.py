import subprocess
import sys
import re
import logging
import errno
import os
from pprint import pformat

from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError

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

    def popen(self, *args, **kw):
        args = list(args)
        args.insert(0, self.cmd)

        kw['stderr'] = subprocess.PIPE
        if self.capture_stdout:
            kw['stdout'] = subprocess.PIPE

        logging.debug("Running " + str(args))
        try:
            return subprocess.Popen(args, **kw)
        except OSError as e:
            if e.errno == errno.ENOENT:
                raise MissingToolError(self.cmd, self.os_pkg)
            raise


    def run(self, *args, **kw):
        p = self.popen(*args, **kw)

        stdout, stderr = p.communicate()
        stdout = stdout.decode(self.encoding)
        stderr = stderr.decode(self.encoding)

        # Hide ignored lines from stderr
        for line in stderr.splitlines(True):
            if self.__should_ignore(line):
                continue
            sys.stderr.write(line)

        return p.returncode, stdout


    def run_check(self, *args, **kw):
        rc, stdout = self.run(*args, **kw)

        if rc != 0:
            raise ToolError(self.cmd, '{} returned {}'.format(self.cmd, rc))

        return stdout




tool_ldd        = ExternTool('ldd', 'binutils')
tool_objcopy    = ExternTool('objcopy', 'binutils')
tool_patchelf   = ExternTool('patchelf', 'patchelf',
                    stderr_ignore = [
                        'working around a Linux kernel bug by creating a hole',
                    ])
tool_strip      = ExternTool('strip', 'binutils')

class LddError(ToolError):
    def __init__(self, message):
        super(LddError, self).__init__('ldd', message)


def get_shobj_deps(path, libpath=[]):
    """Discover the dependencies of a shared object (*.so file)
    """

    # First verify we're dealing with a dynamic ELF file
    ensure_dynamic(path)


    # TODO: Should we use dict(os.environ) instead?
    #       For now, make sure we always pass a clean environment.
    env = {}

    if libpath:
        # Prepend to LD_LIBRARY_PATH
        assert isinstance(libpath, list)
        old_libpath = env.get('LD_LIBRARY_PATH', '')
        env['LD_LIBRARY_PATH'] = ':'.join(libpath + [old_libpath])

    rc, output = tool_ldd.run(path, env=env)

    if rc != 0:
        # There are multiple ways this can happen:
        #
        # $ ldd ./static
        #     not a dynamic executable
        #
        # We avoid this case by ensuring we're looking at a dynamic ELF.
        #
        #
        # $ ldd ./dynamic-musl
        # ./dynamic-musl: error while loading shared libraries: /lib64/libc.so: invalid ELF header
        #
        # GNU libc doesn't like something about the ELF headers of object files
        # produced by musl-libc
        #
        # We simply raise a specific exception and let the caller deal with it.
        raise LddError("Unexpected ldd error ({}): {}".format(rc, output))


    # Example:
    #	linux-vdso.so.1 (0x00007ffe53551000)
    #     or
    #	linux-vdso.so.1 =>  (0x00007ffe53551000)
    #	libc.so.6 => /usr/lib64/libc.so.6 (0x00007f42ac010000)
    #	/lib64/ld-linux-x86-64.so.2 (0x0000557376e75000)
    pat = re.compile(r'\t([\w./+-]*) (?:=> ([\w./+-]*) )?\((0x[0-9a-fA-F]*)\)')

    def parse():
        for line in output.splitlines():
            m = pat.match(line)
            if not m:
                # Some shared objs might have no DT_NEEDED tags (see issue #67)
                if line == '\tstatically linked':
                    break
                raise LddError("Unexpected line in ldd output: " + line)
            libname  = m.group(1)
            libpath  = m.group(2)
            baseaddr = int(m.group(3), 16)

            if libname.startswith('/'):
                # An absolute path here is probably INTERP
                # and ldd shouldn't output the => /abs/path part.
                if libpath:
                    raise LddError("Unexpected line in ldd output: " + line)
                yield libname
            else:
                # A short libname should come from a NEEDED tag
                # and ldd should include the => /abs/path part.
                # If it doesn't, then it's probably linux-vdso*.so
                # or linux-gate.so
                if not libpath:
                    # TODO: This check could be removed/relaxed
                    if libname.startswith('linux-'):
                        continue
                    raise LddError("Unexpected line in ldd output: " + line)
                yield libpath

    return list(parse())



def elf_add_section(elfpath, secname, secfilename):
    tool_objcopy.run_check(
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

    tool_patchelf.run_check(*args)

def strip_elf(path):
    tool_strip.run_check(path)


################################################################################
# Using pyelftools

class StaticELFError(Error):
    """Dynamic operation requested on static executable"""
    def __init__(self, path):
        message = "{} is a static ELF file".format(path)
        super(StaticELFError, self).__init__(message)


class ELFCloser(object):
    def __init__(self, path, mode):
        self.f = open(path, mode)
        self.elf = ELFFile(self.f)

    def __enter__(self):
        return self.elf

    def __exit__(self, *exc_info):
        self.f.close()

def _open_elf(path, mode='rb'):
    try:
        return ELFCloser(path, mode)
    except ELFError as e:
        raise InvalidInputError("{}: Invalid ELF image: {}".format(path, e))


def get_machine(path):
    with _open_elf(path) as elf:
        return elf['e_machine']

def get_prog_interp(path):
    with _open_elf(path) as elf:
        for seg in elf.iter_segments():
            # Amazingly, this is slightly faster than
            # if isinstance(seg, InterpSegment):
            try:
                return seg.get_interp_name()
            except AttributeError:
                continue
        else:
            raise InvalidInputError("{}: not a dynamic executable "
                                    "(no interp segment)".format(path))


def is_dynamic(path):
    with _open_elf(path) as elf:
        for seg in elf.iter_segments():
            if seg['p_type'] == 'PT_DYNAMIC':
                # seg is an instance of DynamicSegment
                return True
        return False


def ensure_dynamic(path):
    if not is_dynamic(path):
        raise StaticELFError(path=path)
