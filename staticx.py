#!/usr/bin/env python3
import argparse
import subprocess
import os
import sys

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



def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('prog',
            help = 'Input program to bundle')
    return ap.parse_args()

def main():
    args = parse_args()

    get_shobj_deps(args.prog)


if __name__ == '__main__':
    try:
        main()
    except AppError as e:
        print("staticx:", e)
        sys.exit(e.exitcode)
