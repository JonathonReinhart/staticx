from __future__ import print_function
import os
import sys

from conftest import custom_tests
from buildutils import cquote

top_dir = Dir('.')
sys.path.append(str(top_dir))

# Set up base environment
base_env = Environment(
    CCFLAGS = [
        '-std=gnu99',
        '-Wall', '-Werror',
        '-Wmissing-prototypes', '-Wstrict-prototypes',
    ],
    BUILD_ROOT = '#scons_build',
    BUILD_DIR = '$BUILD_ROOT/$MODE',
    LIBDIR = '$BUILD_DIR/lib',
    LIBPATH = '$LIBDIR',
    STATICX_VERSION = ARGUMENTS.get('STATICX_VERSION', '<unknown>'),
    CPPDEFINES = dict(
        STATICX_VERSION = cquote('$STATICX_VERSION'),
    ),
)

def get_anywhere(what, default=None):
    return ARGUMENTS.get(what) or os.environ.get(what) or default

def tool_debug(env):
    env['MODE'] = 'debug'
    env.AppendUnique(
        CPPDEFINES = {'DEBUG': 1},
        CCFLAGS = ['-g'],
    )

def tool_release(env):
    env['MODE'] = 'release'
    env.AppendUnique(
        CPPDEFINES = {'NDEBUG': 1},
        CCFLAGS = ['-Os'],
    )

def ModeEnvs(env):
    for t in (tool_debug, tool_release):
        menv = env.Clone(tools=[t])
        yield menv
base_env.AddMethod(ModeEnvs)

def BuildSubdir(env, dirname):
    return env.SConscript(
        dirs = dirname,
        variant_dir = '$BUILD_DIR/' + dirname,
        duplicate = False,
        exports = dict(env=env.Clone()),
    )
base_env.AddMethod(BuildSubdir)


conf = base_env.Configure(custom_tests=custom_tests)
has_nss = conf.CheckNSS()
conf.Finish()


################################################################################
# Bootloader
bootloader_env = base_env.Clone()
cc = get_anywhere('BOOTLOADER_CC')
if cc:
    bootloader_env['CC'] = cc

for env in bootloader_env.ModeEnvs():
    env.Install('$LIBDIR', env.BuildSubdir('libtar'))
    env.Install('$LIBDIR', env.BuildSubdir('libxz'))
    env.InstallAs('#staticx/assets/$MODE/bootloader', env.BuildSubdir('bootloader'))


################################################################################
# nssfix
if has_nss:
    for env in base_env.ModeEnvs():
        env.InstallAs('#staticx/assets/$MODE/libnssfix.so', env.BuildSubdir('libnssfix'))
else:
    print("WARNING: NSS not available; staticx will not include nssfix for GLIBC programs!")
