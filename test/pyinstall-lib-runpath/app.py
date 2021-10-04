#!/usr/bin/env python3
from ctypes import *
from pathlib import Path

mydir = Path(__file__).parent

dll = CDLL(mydir / 'shlib.so')

dll.foo.argtypes = ()
dll.foo.restype = c_int

print("foo() =>", dll.foo())
