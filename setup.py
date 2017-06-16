#!/usr/bin/env python
# Derived from https://github.com/JonathonReinhart/scuba
from __future__ import print_function
import staticx.version
from setuptools import setup, Command
from distutils.command.build import build
import os.path
from subprocess import check_call


class build_bootloader(Command):
    description = "Build staticx bootloader binary"

    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass

    def run(self):
        check_call(['scons'])


class build_hook(build):
    def run(self):
        self.run_command('build_bootloader')
        build.run(self)


setup(
    name = 'staticx',
    version = staticx.version.__version__,
    description = 'Build static self-extracting app from dynamic executable',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Topic :: Software Development :: Build Tools',
    ],
    license = 'MIT',
    author = 'Jonathon Reinhart',
    author_email = 'jonathon.reinhart@gmail.com',
    url = 'https://github.com/JonathonReinhart/staticx',
    packages = ['staticx'],
    package_data = {
        'staticx': [
            'bootloader',
        ],
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
        ]
    },
    install_requires = [
    ],

    # http://stackoverflow.com/questions/17806485
    # http://stackoverflow.com/questions/21915469
    # PyInstaller setup.py
    cmdclass = {
        'build_bootloader': build_bootloader,
        'build':            build_hook,
    },
)
