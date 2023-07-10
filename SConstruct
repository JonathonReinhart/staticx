from __future__ import print_function
import os

from conftest import custom_tests

def quote(s, q='"'):
    return q + s + q

# Set up base environment
base_env = Environment(
    CCFLAGS = [
        '-std=gnu99',
        '-Wall', '-Werror',
        '-Wmissing-prototypes', '-Wstrict-prototypes',
    ],
    LINKFLAGS = [   # gcc is linker
        '-Wl,--fatal-warnings',
    ],
    BUILD_ROOT = '#scons_build',
    BUILD_DIR = '$BUILD_ROOT/$MODE',
    LIBDIR = '$BUILD_DIR/lib',
    LIBPATH = '$LIBDIR',
    STATICX_VERSION = ARGUMENTS.get('STATICX_VERSION', '<unknown>'),
    CPPDEFINES = dict(
        STATICX_VERSION = quote(quote('$STATICX_VERSION', '"'), "'"),
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


###########
# Configure
conf = base_env.Configure(custom_tests=custom_tests)

# Does our default libc have NSS?
conf.env["HAS_NSS"] = conf.CheckNSS()

# Starting in GLIBC 2.34, some NSS modules (files, dns) can be built-in to
# libc.so. Determine which ones are builtin. See #245.
conf.env["NSS_MODS_BUILTIN"] = []
if conf.env["HAS_NSS"]:
    maybe_builtin_nss_modules = ["files", "dns"]
    for mod in maybe_builtin_nss_modules:
        libname = "libnss_" + mod
        # It the library doesn't exist, assume it is built-in.
        if not conf.BasicCheckLib(libname):
            conf.env.Append(NSS_MODS_BUILTIN=libname)
    print("Builtin NSS modules:", conf.env["NSS_MODS_BUILTIN"])

base_env = conf.Finish()

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
if env['HAS_NSS']:
    for env in base_env.ModeEnvs():
        env.InstallAs('#staticx/assets/$MODE/libnssfix.so', env.BuildSubdir('libnssfix'))
else:
    print("WARNING: NSS not available; staticx will not include nssfix for GLIBC programs!")
