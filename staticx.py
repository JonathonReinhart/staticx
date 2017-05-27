#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys
import re

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


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('prog',
            help = 'Input program to bundle')
    return ap.parse_args()

def main():
    args = parse_args()

    for lib in get_shobj_deps(args.prog):
        print(lib)


if __name__ == '__main__':
    try:
        main()
    except AppError as e:
        print("staticx:", e)
        sys.exit(e.exitcode)
