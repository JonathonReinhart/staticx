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

    # Travis builds
    # If we're not building for a tag, then append the build number
    build_num = os.getenv('TRAVIS_BUILD_NUMBER')
    build_tag = os.getenv('TRAVIS_TAG')
    if (not build_tag) and (build_num != None):
        return '{}.{}'.format(staticx.version.BASE_VERSION, build_num)

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
            'STATICX_VERSION={}'.format(get_dynamic_version()),
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
        raise UnsupportedPlatformError("OS {!r} unsupported by staticx".format(osname))

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

    return 'manylinux1_{}'.format(machine)

################################################################################

def read_project_file(path):
    proj_dir = os.path.dirname(__file__)
    path = os.path.join(proj_dir, path)
    with open(path, 'r') as f:
        return f.read()

setup(
    name = 'staticx',
    version = get_dynamic_version(),
    description = 'Build static self-extracting app from dynamic executable',
    python_requires='>=3.5',
    long_description = read_project_file('README.md'),
    long_description_content_type = 'text/markdown',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Build Tools',
    ],
    license = 'GPL v2 with special exception allowing StaticX to build and'
              ' distribute non-free programs',
    author = 'Jonathon Reinhart',
    author_email = 'jonathon.reinhart@gmail.com',
    url = 'https://github.com/JonathonReinhart/staticx',
    packages = find_packages(),
    package_data = {
        'staticx': ['assets/*/*'],
    },

    # Ugh.
    # https://github.com/JonathonReinhart/staticx/issues/22
    # https://github.com/JonathonReinhart/scuba/issues/77
    # https://github.com/pypa/setuptools/issues/1064
    include_package_data = True,

    zip_safe = False,   # http://stackoverflow.com/q/24642788/119527
    entry_points = {
        'console_scripts': [
            'staticx = staticx.__main__:main',
            'sx-extract = staticx.extract:main',
        ]
    },
    install_requires = [
        'pyelftools',
    ],

    # http://stackoverflow.com/questions/17806485
    # http://stackoverflow.com/questions/21915469
    # PyInstaller setup.py
    cmdclass = {
        'build_bootloader': build_bootloader,
        'build':            build_hook,
        'bdist_wheel':      bdist_wheel_hook,
    },
)
