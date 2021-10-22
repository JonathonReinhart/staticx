#!/usr/bin/env python3
from ctypes import *
from pathlib import Path

mydir = Path(__file__).parent

libfoo = CDLL(mydir / 'libfoo.so')

libfoo.foo.argtypes = ()
libfoo.foo.restype = c_int

print("foo() =>", libfoo.foo())
