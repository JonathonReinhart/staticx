#!/usr/bin/env python3
import pytest
import os
from tempfile import NamedTemporaryFile
from staticx import elf
from staticx.errors import MissingToolError
from staticx.utils import make_executable


class TestExternTool:
    def test_nonexist(self):
        tool_bs = elf.ExternTool('madeupthing1738', 'bs')
        with pytest.raises(MissingToolError):
            tool_bs.run_check()

    def test_basic(self):
        tool_true = elf.ExternTool('true', 'na')
        tool_true.run_check()

    def test_strderr_ignore(self, capfd):
        # https://docs.pytest.org/en/stable/capture.html#accessing-captured-output-from-a-test-function
        with NamedTemporaryFile('w', suffix='.sh', delete=False) as f:
            f.write('#!/bin/bash\n')
            f.write('echoerr() { echo "$@" 1>&2; }\n')
            f.write('echoerr one\n')
            f.write('echoerr two\n')
            f.write('echoerr three\n')

        try:
            make_executable(f.name)
            tool_foo = elf.ExternTool(f.name, 'na',
                    stderr_ignore = [
                        'two',
                    ])
            tool_foo.run()
        finally:
            os.remove(f.name)

        captured = capfd.readouterr()
        assert captured.err == 'one\nthree\n'


class TestLdd:
    def _test(self, output, exp):
        res = list(elf._parse_ldd_output(output))
        assert res == exp 

    def test_ubuntu_1604(self):
        # https://github.com/JonathonReinhart/staticx/pull/102#issuecomment-569874924
        output = (
            "\tlinux-vdso.so.1 =>  (0x00007ffdacbdd000)\n"
	    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f03d10aa000)\n"
	    "\t/lib64/ld-linux-x86-64.so.2 (0x00007f03d1474000)\n")
        exp = [
	    "/lib/x86_64-linux-gnu/libc.so.6",
	    "/lib64/ld-linux-x86-64.so.2",
        ]
        self._test(output, exp)

    def test_ubuntu_1604_i386(self):
        output = (
	    "\tlinux-gate.so.1 =>  (0xf7ef7000)\n"
	    "\tlibc.so.6 => /lib/i386-linux-gnu/libc.so.6 (0xf7d3b000)\n"
	    "\t/lib/ld-linux.so.2 (0xf7ef9000)\n")
        exp = [
	    "/lib/i386-linux-gnu/libc.so.6",
	    "/lib/ld-linux.so.2",
        ]
        self._test(output, exp)

    def test_debian_10(self):
        output = (
	    "\tlinux-vdso.so.1 (0x00007fff413cf000)\n"
	    "\tlibc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f6916ead000)\n"
            "\t/lib64/ld-linux-x86-64.so.2 (0x00007f69170a7000)\n")
        exp = [
            "/lib/x86_64-linux-gnu/libc.so.6",
            "/lib64/ld-linux-x86-64.so.2",
        ]
        self._test(output, exp)


    def test_arch(self):
        # https://github.com/JonathonReinhart/staticx/issues/116
        output = (
            "\tlinux-vdso.so.1 (0x00007ffc431fc000)\n"
            "\tlibdl.so.2 => /usr/lib/libdl.so.2 (0x00007f1de6361000)\n"
	    "\tlibz.so.1 => /usr/lib/libz.so.1 (0x00007f1de6347000)\n"
	    "\tlibc.so.6 => /usr/lib/libc.so.6 (0x00007f1de6180000)\n"
	    "\t/lib64/ld-linux-x86-64.so.2 => /usr/lib64/ld-linux-x86-64.so.2 (0x00007f1de63ac000)\n")
        exp = [
            "/usr/lib/libdl.so.2",
	    "/usr/lib/libz.so.1",
	    "/usr/lib/libc.so.6",
	    "/usr/lib64/ld-linux-x86-64.so.2",
        ]
        self._test(output, exp)

    def test_raspios(self):
        # https://github.com/JonathonReinhart/staticx/issues/209
        output = (
            "\tlinux-vdso.so.1 (0xbeee8000)\n"
	    "\t/usr/lib/arm-linux-gnueabihf/libarmmem-${PLATFORM}.so => /usr/lib/arm-linux-gnueabihf/libarmmem-v7l.so (0xb6eeb000)\n"
	    "\tlibdl.so.2 => /lib/arm-linux-gnueabihf/libdl.so.2 (0xb6ed7000)\n"
	    "\tlibz.so.1 => /lib/arm-linux-gnueabihf/libz.so.1 (0xb6eac000)\n"
	    "\tlibpthread.so.0 => /lib/arm-linux-gnueabihf/libpthread.so.0 (0xb6e80000)\n"
	    "\tlibc.so.6 => /lib/arm-linux-gnueabihf/libc.so.6 (0xb6d2c000)\n"
	    "\t/lib/ld-linux-armhf.so.3 (0xb6f00000)\n")
        exp = [
            "/usr/lib/arm-linux-gnueabihf/libarmmem-v7l.so",
            "/lib/arm-linux-gnueabihf/libdl.so.2",
            "/lib/arm-linux-gnueabihf/libz.so.1",
            "/lib/arm-linux-gnueabihf/libpthread.so.0",
            "/lib/arm-linux-gnueabihf/libc.so.6",
            "/lib/ld-linux-armhf.so.3",
        ]
        self._test(output, exp)


def test_is_dynamic_elf_handles_non_elf():
    with NamedTemporaryFile('wb', suffix='.bin') as f:
        f.write(b"\x11\x22\x33\x44")
        f.flush()

        assert not elf.is_dynamic_elf(f.name)


def test_is_dynamic_elf_handles_elf():
    assert elf.is_dynamic_elf("/bin/true")
