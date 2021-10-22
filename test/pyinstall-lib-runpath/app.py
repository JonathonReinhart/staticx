#!/usr/bin/env python3
from ctypes import *
from pathlib import Path

mydir = Path(__file__).parent

libfoo = CDLL(mydir / 'libfoo.so')
libbar = CDLL(mydir / 'libbar.so')

def setup_prototype(func, restype, *argtypes):
    func.restype = restype
    func.argtypes = argtypes

setup_prototype(libfoo.foo, c_int)
setup_prototype(libbar.bar, c_int)

print("foo() =>", libfoo.foo())
print("bar() =>", libbar.bar())
