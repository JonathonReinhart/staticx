#!/usr/bin/env python3
from staticx import elf

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
