#!/usr/bin/env python
# Derived from https://github.com/JonathonReinhart/scuba
from setuptools import setup, Command, find_packages
from wheel.bdist_wheel import bdist_wheel
from distutils.command.build import build
import os
import sys
from subprocess import check_call


################################################################################
# Dynamic versioning

def get_dynamic_version():
    import staticx.version

    # CI builds
    # If CI_VERSION_BUILD_NUMBER is set, append that to the base version
    build_num = os.getenv("CI_VERSION_BUILD_NUMBER")
    if build_num:
        return f'{staticx.version.BASE_VERSION}.{build_num}'

    # Otherwise, use the auto-versioning
    return staticx.version.__version__


################################################################################
# Commands / hooks

class build_bootloader(Command):
    description = "Build staticx bootloader binary"

    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        args = [
            'scons',
            '-Q',       # Quiet output (except for build status)
            f'STATICX_VERSION={get_dynamic_version()}',
        ]
        check_call(args)


class build_hook(build):
    def run(self):
        self.run_command('build_bootloader')
        build.run(self)


class bdist_wheel_hook(bdist_wheel):
    def finalize_options(self):
        self.plat_name = get_platform()     # Equivalent to passing --plat-name
        super().finalize_options()


class UnsupportedPlatformError(Exception):
    pass

def get_platform():
    """Get platform string (e.g. "manylinux1_x86_64")

    Staticx itself is a pure python package, but it includes binary assets
    which are OS/machine dependent. Thus, staticx wheels shouldn't be tagged
    with platform of "any", which is the default behavior when setup.py doesn't
    include any Python extensions.

    There are various ways to change this behavior, none of which works well
    for staticx:
    1) Pass --plat-name to `setup.py bdist_wheel`.
       This gets in the way of external tooling (e.g. Travis 'deploy')
    2) Include a dummy Extension: https://stackoverflow.com/a/53463910
       This causes undue problems becuase it sets the Python ABI field also,
       which staticx doesn't care about.

    So instead, we take care of it ourselves.

    While staticx isn't really built in the typical 'manylinux1' fashion,
    it identifies as 'manylinux1' for PyPI binary wheel compatibility.

    Rationale: staticx assets follow stricter compatibility rules than
    manylinux1:
    - bootloader is statically-linked
    - libnsskill.so is GLIBC-specific and version-agnostic
    """
    uname = os.uname()

    # Apply the same conversions as distutils.util.get_platform()
    osname = uname.sysname.lower().replace('/', '')
    machine = uname.machine.replace(' ', '_').replace('/', '-')

    # Check compatibility
    if osname != "linux":
        # Right now staticx only supports Linux
        raise UnsupportedPlatformError(f"OS {osname!r} unsupported by staticx")

    # Adjust machine if necessary
    #
    # This applies to a 32-bit Python interpreter running on a 64-bit kernel.
    # We assume that the compiler is also targetting 32-bit, otherwise Python
    # won't match the UINTPTR_MAX check in bootloader/elfutil.h
    #
    # See:
    #   https://github.com/pypa/pip/pull/3497#discussion_r54870308
    #   https://github.com/pypa/wheel/commit/b9dbb6fa257c
    if machine == "x86_64" and sys.maxsize == 0x7fffffff:
        machine = "i686"

    return f'manylinux1_{machine}'

################################################################################

setup(
    #####
    # Dynamic core metadata, in addition to pyproject.toml [project]
    version = get_dynamic_version(),
    #####
    # Setuptools-specific config
    # We could put this in pyproject.toml [tool.setuptools], but choose not to:
    # - The functionality is still in beta and requires setuptools >= 61.0.0
    # - We need setup.py to provide build_hook, so we might as well keep all
    #   setuptools-specific config here, in one file.
    packages=find_packages(),
    package_data = {
        'staticx': ['assets/*/*'],
    },
    include_package_data=True,  # https://github.com/pypa/setuptools/issues/1064
    zip_safe = False,   # http://stackoverflow.com/q/24642788/119527
    # http://stackoverflow.com/questions/17806485
    # http://stackoverflow.com/questions/21915469
    # PyInstaller setup.py
    cmdclass = {
        'build_bootloader': build_bootloader,
        'build':            build_hook,
        'bdist_wheel':      bdist_wheel_hook,
    },
)
