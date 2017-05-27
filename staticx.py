#!/usr/bin/env python3
import argparse
import subprocess
import tarfile
import shutil
from tempfile import NamedTemporaryFile
import os
import sys
import re

ARCHIVE_SECTION = ".staticx.archive"
INTERP_FILENAME = ".staticx.interp"
PROG_FILENAME   = ".staticx.prog"

class AppError(Exception):
    def __init__(self, message, exitcode=2):
        super().__init__(message)
        self.exitcode = exitcode

def get_shobj_deps(path):
    try:
        output = subprocess.check_output(['ldd', path])
    except FileNotFoundError:
        raise AppError("Couldn't find 'ldd'. Is 'binutils' installed?")
    except subprocess.CalledProcessError as e:
        raise AppError("'ldd' failed")

    # Example:
    #	libc.so.6 => /usr/lib64/libc.so.6 (0x00007f42ac010000)
    #	/lib64/ld-linux-x86-64.so.2 (0x0000557376e75000)
    pat = re.compile('\t([\w./-]*) (?:=> ([\w./-]*) )?\((0x[0-9a-fA-F]*)\)')

    for line in output.decode('ascii').splitlines():
        m = pat.match(line)
        if not m:
            raise ValueError("Unexpected line in ldd output: " + line)
        libname  = m.group(1)
        libpath  = m.group(2)
        baseaddr = int(m.group(3), 16)

        libpath = libpath or libname
        yield libpath

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
    f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')

    with tarfile.open(fileobj=f, mode='w') as tar:

        # Add the program
        arcname = PROG_FILENAME
        print("    Adding {} as {}".format(prog, arcname))
        tar.add(prog, arcname=arcname)

        # Add all of the libraries
        for lib in get_shobj_deps(prog):
            if lib.startswith('linux-vdso.so'):
                continue

            arcname = os.path.basename(lib)
            print("    Adding {} as {}".format(lib, arcname))
            tar.add(lib, arcname=arcname)

            if os.path.islink(lib):
                reallib = get_symlink_target(lib)
                arcname = os.path.basename(reallib)
                print("    Adding {} as {}".format(reallib, arcname))
                tar.add(reallib, arcname=arcname)
                # TODO: Recursively handle symlinks


            # TODO: Look up INTERP from prog instead of assuming ld-linux
            if 'ld-linux' in lib:
                tar.addfile(make_symlink_TarInfo(INTERP_FILENAME, lib))

    f.flush()
    return f


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('prog',
            help = 'Input program to bundle')
    ap.add_argument('output',
            help = 'Output path')
    ap.add_argument('--bootloader',
            help = 'Path to bootloader')
    return ap.parse_args()

def main():
    args = parse_args()

    shutil.copy2(args.bootloader, args.output)

    with generate_archive(args.prog) as ar:
        elf_add_section(args.output, ARCHIVE_SECTION, ar.name)


if __name__ == '__main__':
    try:
        main()
    except AppError as e:
        print("staticx:", e)
        sys.exit(e.exitcode)
