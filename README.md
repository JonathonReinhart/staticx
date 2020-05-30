StaticX [![Build Status](https://travis-ci.org/JonathonReinhart/staticx.svg?branch=master)](https://travis-ci.org/JonathonReinhart/staticx) [![PyPI](https://img.shields.io/pypi/v/staticx.svg)](https://pypi.python.org/pypi/staticx)
=======
Bundle dynamic executables with their library dependencies so they can be run
anywhere, just like a static executable.

## Requirements
StaticX currently works only with Linux 64-bit dynamic executables.


The following external tools need to be installed to run StaticX:
- `ldd` - Part of GNU C Library
- `readelf` - Part of binutils
- `objcopy` - Part of binutils
- [`patchelf`][patchelf]
   - Packages available for Debian 8+, Fedora 14+, others
   - install with `pip install patchelf-wrapper`

The following additional tools must be installed to build StaticX from source:
- `scons`
- [`musl-libc`][musl-libc] *(optional)*


## Installation

### From PyPI
StaticX is [avaiable on PyPI](https://pypi.python.org/pypi/staticx).
The wheels are built on Travis CI and include a bootloader built with
musl-libc.

You can install using Pip.
StaticX is compatible with Python Python 3.5+ (`pip3`):
```
sudo pip3 install staticx
```

### From source

If you have musl libc installed, you can use it to build the staticx
bootloader, resulting in smaller, better binaries. To do so, set the
`BOOTLOADER_CC` environment variable to your `musl-gcc` wrapper path
wehn invoking `pip` or `setup.py`:

```
sudo BOOTLOADER_CC=/usr/local/musl/bin/musl-gcc pip3 install https://github.com/JonathonReinhart/staticx/archive/master.zip
```

```
cd staticx
sudo BOOTLOADER_CC=/usr/local/musl/bin/musl-gcc pip3 install .
```

## Usage

Basic wrapping of an executable
```
staticx /path/to/exe /path/to/output
```

Including additional library files with the package (any number can be specified by repeating the -l option)
```
staticx -l /path/to/fancy/library /path/to/exe /path/to/output
```

## Run-time Information
StaticX sets the following environment variables for the wrapped user program:
- `STATICX_BUNDLE_DIR`: The absolute path of the "bundle" directory, the
  temporary dir where the archive has been extracted.
- `STATICX_PROG_PATH`: The absolute path of the program being executed.


## License
This software is released under the GPLv2, with an exception allowing the
bootloader to be distributed. See [LICENSE.txt](LICENSE.txt) for more details.


[patchelf]: https://nixos.org/patchelf.html
[musl-libc]: https://www.musl-libc.org/
[#45]: https://github.com/JonathonReinhart/staticx/issues/45
