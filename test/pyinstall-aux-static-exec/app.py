import argparse
import os
import sys
import subprocess

from auxlist import aux_apps

def get_resource_dir():
    default = os.path.dirname(os.path.abspath(__file__))
    return getattr(sys, '_MEIPASS', default)


def get_resource(name):
    return os.path.join(get_resource_dir(), name)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip', action='append', default=[],
            help="aux apps to skip")
    return ap.parse_args()


def main():
    args = parse_args()

    # Run whichever binaries were compiled
    for name in aux_apps:
        if name in args.skip:
            continue

        auxapp = get_resource(name)

        # Try to run the file if it was included
        if os.path.isfile(auxapp):
            subprocess.check_call([auxapp])

if __name__ == '__main__':
    main()
