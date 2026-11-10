#!/usr/bin/env python3
from ctypes import CDLL, c_int
from pathlib import Path

mydir = Path(__file__).parent

libfoo_path = (mydir / "libfoo.so").absolute()
assert libfoo_path.exists()

libfoo = CDLL(libfoo_path)


def setup_prototype(func, restype, *argtypes):
    func.restype = restype
    func.argtypes = argtypes


setup_prototype(libfoo.foo, c_int)
setup_prototype(libfoo.foobar, c_int)

print("foo() =>", libfoo.foo())
print("foobar() =>", libfoo.foobar())
