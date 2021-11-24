Installation
============

Requirements
------------
StaticX currently works only with Linux 64-bit dynamic executables.

The following external tools must be installed to use StaticX, all of which are
readily available in the package manager of most Linux distributions:

- ``ldd`` -- Part of GNU C Library
- ``readelf`` -- Part of binutils
- ``objcopy`` -- Part of binutils
- ``patchelf`` -- https://github.com/NixOS/patchelf

   - Distro packages available for Debian 8+, Fedora 14+, others (preferred)
   - Or install with ``pip install patchelf-wrapper``

The following additional tools must be installed to build StaticX from source:

- ``scons``
- `musl libc`_ *(optional)*

StaticX is compatible with Python 3.5+.


Install via pip
---------------
StaticX is hosted at `PyPI`_, and the wheels include a bootloader built with
`musl libc`_.

Installation via pip is the preferred method::

    pip3 install staticx


Install from source
-------------------
If you have `musl libc`_ installed, you can use it to build the staticx
bootloader, resulting in smaller, better binaries. To do so, set the
``BOOTLOADER_CC`` environment variable to your ``musl-gcc`` wrapper path when
invoking `pip` or `setup.py`::

    BOOTLOADER_CC=/usr/local/musl/bin/musl-gcc pip3 install https://github.com/JonathonReinhart/staticx/archive/master.zip

Or::

    cd staticx
    BOOTLOADER_CC=/usr/local/musl/bin/musl-gcc pip3 install .


.. _PyPI: https://pypi.python.org/pypi/staticx
.. _musl libc: https://www.musl-libc.org/
