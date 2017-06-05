from __future__ import print_function
import os
import sys

def get_resource_dir():
    default = os.path.dirname(os.path.abspath(__file__))
    return getattr(sys, '_MEIPASS', default)
    
print("Hello world! Resource dir: {}".format(get_resource_dir()))
