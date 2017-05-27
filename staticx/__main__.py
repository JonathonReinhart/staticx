import argparse
import sys

from .api import generate

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
    generate(args.prog, args.output, args.bootloader)


if __name__ == '__main__':
    try:
        main()
    except AppError as e:
        print("staticx:", e)
        sys.exit(e.exitcode)
