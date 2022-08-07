#!/bin/bash
export BOOTLOADER_CC=musl-gcc

rm -rf build dist scons_build staticx/assets
python3 setup.py sdist bdist_wheel
