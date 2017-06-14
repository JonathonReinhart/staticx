#!/usr/bin/env python
# Derived from https://github.com/JonathonReinhart/scuba
from __future__ import print_function
import staticx.version
from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.sdist import sdist
import os.path
from subprocess import check_call


def make_first(command_subclass):
    """A decorator for classes subclassing one of the setuptools commands.

    It modifies the run() method to run make first
    """
    # https://blog.niteoweb.com/setuptools-run-custom-code-in-setup-py/
    orig_run = command_subclass.run

    def modified_run(self):
        check_call(['scons'])
        orig_run(self)

    command_subclass.run = modified_run
    return command_subclass


cmdclass_hooks = {}

@make_first
class build_py_hook(build_py):
    pass
cmdclass_hooks['build_py'] = build_py_hook

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None

if bdist_wheel:
    @make_first
    class bdist_wheel_hook(bdist_wheel):
        pass
    cmdclass_hooks['bdist_wheel'] = bdist_wheel_hook



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
    cmdclass = cmdclass_hooks,
)
