#!/usr/bin/env python3
from ctypes import *
from pathlib import Path

mydir = Path(__file__).parent

libfoo_path = (mydir / 'libfoo.so').absolute()
libbar_path = (mydir / 'libbar.so').absolute()

assert libfoo_path.exists()
assert libbar_path.exists()

libfoo = CDLL(libfoo_path)
libbar = CDLL(libbar_path)

def setup_prototype(func, restype, *argtypes):
    func.restype = restype
    func.argtypes = argtypes

setup_prototype(libfoo.foo, c_int)
setup_prototype(libbar.bar, c_int)

print("foo() =>", libfoo.foo())
print("bar() =>", libbar.bar())
