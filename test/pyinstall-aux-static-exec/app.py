from __future__ import print_function
import os
import sys
import subprocess

def get_resource_dir():
    default = os.path.dirname(os.path.abspath(__file__))
    return getattr(sys, '_MEIPASS', default)


def get_resource(name):
    return os.path.join(get_resource_dir(), name)


for name in ('aux-dynamic', 'aux-static'):
    auxapp = get_resource(name)
    subprocess.check_call([auxapp])
