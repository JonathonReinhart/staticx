import argparse
import sys

from .api import generate
from .errors import Error

def parse_args():
    ap = argparse.ArgumentParser(prog='staticx')
    ap.add_argument('prog',
            help = 'Input program to bundle')
    ap.add_argument('output',
            help = 'Output path')
    ap.add_argument('--bootloader',
            help = argparse.SUPPRESS)
    return ap.parse_args()

def main():
    args = parse_args()
    try:
        generate(args.prog, args.output, args.bootloader)
    except Error as e:
        print("staticx:" ,e)
        sys.exit(2)

if __name__ == '__main__':
    main()
