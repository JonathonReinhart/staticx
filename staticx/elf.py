import subprocess
import sys
import re
import locale
import logging
import errno
import os
from pprint import pformat

from elftools.elf.elffile import ELFFile
from elftools.common.exceptions import ELFError

from .errors import *
from .utils import coerce_sequence

class ExternTool:
    def __init__(self, cmd, os_pkg, stderr_ignore=[], encoding=None):
        self.cmd = cmd
        self.os_pkg = os_pkg
        self.stderr_ignore = stderr_ignore
        if encoding is None:
            # Same as subprocess.run()
            encoding = locale.getpreferredencoding(False)
        self.encoding = encoding

    def __should_ignore(self, line):
        for ignore in self.stderr_ignore:
            if ignore in line:
                return True
        return False

    def run(self, *args, **kw):
        args = list(args)
        args.insert(0, self.cmd)

        logging.debug("Running " + str(args))
        try:
            r = subprocess.run(
                args = args,

                #capture_output = True,         # TODO: Python 3.7
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,

                **kw)
        except FileNotFoundError:
            raise MissingToolError(self.cmd, self.os_pkg)

        # TODO: Python 3.6: Simply set encoding in run() call
        r.stdout = r.stdout.decode(self.encoding)
        r.stderr = r.stderr.decode(self.encoding)

        # Hide ignored lines from stderr
        for line in r.stderr.splitlines(True):
            if self.__should_ignore(line):
                continue
            sys.stderr.write(line)

        return r.returncode, r.stdout


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
                    ],
                    # They literally have "e2 80 98" in their source file
                    encoding='utf-8',
                    )
tool_strip      = ExternTool('strip', 'binutils')

class LddError(ToolError):
    def __init__(self, message):
        super().__init__('ldd', message)


def _parse_ldd_output(output):
    # Example:
    #	linux-vdso.so.1 (0x00007ffe53551000)
    #     or
    #	linux-vdso.so.1 =>  (0x00007ffe53551000)
    #	libc.so.6 => /usr/lib64/libc.so.6 (0x00007f42ac010000)
    #	/lib64/ld-linux-x86-64.so.2 (0x0000557376e75000)
    #     or
    #   /lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007f1de63ac000)
    pat = re.compile(r'\t([\w./+-]*) (?:=> ([\w./+-]*) )?\((0x[0-9a-fA-F]*)\)')

    for line in output.splitlines():
        m = pat.match(line)
        if not m:
            # Some shared objs might have no DT_NEEDED tags (see issue #67)
            if line == '\tstatically linked':
                break
            raise LddError("Unexpected line in ldd output: " + line)
        libname  = m.group(1)
        resolved = m.group(2)
        baseaddr = int(m.group(3), 16)

        if resolved:
            # ldd outupt a resolved symlink, use that
            libpath = resolved
        elif libname.startswith('/'):
            # The library directly referenced an absolute path, use that
            libpath = libname
        else:
            # Assume an unresolved non-absolute library name is synthetic
            # like linux-vdso*.so or linux-gate.so which should be ignored
            # TODO: This check could be removed/relaxed
            if not libname.startswith('linux-'):
                raise LddError("Unexpected unresolved libname: " + libname)
            logging.debug("Ignoring synthetic library: " + libname)
            continue

        # The library path must be absolute
        if not libpath.startswith('/'):
            raise LddError("Unexpected non-absolute libpath: " + libpath)
        yield libpath


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

    return list(_parse_ldd_output(output))



def elf_add_section(elfpath, secname, secfilename):
    tool_objcopy.run_check(
        '--add-section', '{}={}'.format(secname, secfilename),
        elfpath)


def elf_dump_section(elfpath, secname, outpath):
    # https://stackoverflow.com/a/3925113/119527
    tool_objcopy.run_check(
        '-O', 'binary',
        '--only-section', secname,
        '--set-section-flags', '{}={}'.format(secname, 'alloc'),
        elfpath, outpath)



def patch_elf(path, interpreter=None, rpath=None, force_rpath=False, no_default_lib=False, add_needed=None):
    args = []
    if interpreter:
        args += ['--set-interpreter', interpreter]
    if rpath:
        args += ['--set-rpath', rpath]
    if force_rpath:
        # There is a bug in patchelf that requires --remove-rpath to be used
        # first before --force-rpath is effective.
        # https://github.com/NixOS/patchelf/issues/94
        # This was fixed in v0.11 but that's newer than Debian Buster.
        tool_patchelf.run_check('--remove-rpath', path)

        args.append('--force-rpath')
    if add_needed:
        for lib in coerce_sequence(add_needed):
            args += ['--add-needed', lib]
    args.append(path)

    tool_patchelf.run_check(*args)

    # There is a bug in patchelf that requires the --force-rpath and
    # --no-default-lib steps to be run in separate invocations.
    # https://github.com/NixOS/patchelf/issues/223
    if no_default_lib:
        tool_patchelf.run_check('--no-default-lib', path)


def strip_elf(path):
    tool_strip.run_check(path)


################################################################################
# Using pyelftools

class StaticELFError(Error):
    """Dynamic operation requested on static executable"""
    def __init__(self, path):
        message = "{} is a static ELF file".format(path)
        super().__init__(message)


class ELFCloser:
    def __init__(self, path, mode):
        self.f = open(path, mode)
        self.elf = ELFFile(self.f)

    def __enter__(self):
        return self.elf

    def __exit__(self, *exc_info):
        self.f.close()

def open_elf(path, mode='rb'):
    try:
        return ELFCloser(path, mode)
    except ELFError as e:
        raise InvalidInputError("{}: Invalid ELF image: {}".format(path, e))


def get_section(elf, sectype):
    for sec in elf.iter_sections():
        if isinstance(sec, sectype):
            return sec
    raise KeyError("Can't find section of type {}".format(sectype))


def get_machine(path):
    with open_elf(path) as elf:
        return elf['e_machine']

def get_prog_interp(path):
    with open_elf(path) as elf:
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
    with open_elf(path) as elf:
        for seg in elf.iter_segments():
            if seg['p_type'] == 'PT_DYNAMIC':
                # seg is an instance of DynamicSegment
                return True
        return False


def ensure_dynamic(path):
    if not is_dynamic(path):
        raise StaticELFError(path=path)
