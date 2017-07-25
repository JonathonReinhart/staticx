from __future__ import print_function
import argparse
import sys
import logging

from .api import generate
from .errors import Error
from .version import __version__

def parse_args():
    ap = argparse.ArgumentParser(prog='staticx')

    # Positional arguments
    ap.add_argument('prog',
            help = 'Input program to bundle')
    ap.add_argument('output',
            help = 'Output path')

    # Operational options
    ap.add_argument('-l', dest='libs', action='append',
            help = 'Add additional libraries (absolute paths)')
    ap.add_argument('--strip', action='store_true',
            help = 'Strip binaries before adding to archive (reduces size)')
    ap.add_argument('--no-compress', action='store_true',
            help = "Don't compress the archive (increases size)")

    # Special / output-related options
    ap.add_argument('-V', '--version', action='version',
            version = '%(prog)s ' + __version__)
    ap.add_argument('--loglevel', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            default='WARNING',
            help = 'Set the logging level (default: %(default)s)')

    # Hidden arguments (for development / testing)
    ap.add_argument('--bootloader',
            help = argparse.SUPPRESS)
    return ap.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=args.loglevel)

    try:
        generate(args.prog, args.output,
                libs = args.libs,
                bootloader = args.bootloader,
                strip = args.strip,
                compress = not args.no_compress,
                )
    except Error as e:
        print("staticx: " + str(e))
        sys.exit(2)

if __name__ == '__main__':
    main()
