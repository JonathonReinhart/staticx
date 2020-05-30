from cffi import FFI
import os
import sys

def main():
    ffi = FFI()
    ffi.cdef("""
      int printf(const char *, ...);
    """)

    if False:
        # use a C compiler: verify the decl above is right
        libc = ffi.verify()

    libc = ffi.dlopen(None)

    libc.printf(b"Hello, %s!\n",
            ffi.new("char[]", b"world"),
            )

if __name__ == '__main__':
    print("PID:", os.getpid())
    print("MEIPASS:", getattr(sys, '_MEIPASS', '<not set>'))

    main()
