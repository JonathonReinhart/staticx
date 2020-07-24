import os

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
    LIBPATH = '$LIBDIR'
)

def get_anywhere(env, what):
    return ARGUMENTS.get(what) or os.environ.get(what) or env[what]

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


################################################################################
# Bootloader
bootloader_env = base_env.Clone()
bootloader_env['CC'] = get_anywhere(bootloader_env, 'CC')

for env in bootloader_env.ModeEnvs():
    env.Install('$LIBDIR', env.BuildSubdir('libtar'))
    env.Install('$LIBDIR', env.BuildSubdir('libxz'))
    env.InstallAs('#staticx/assets/$MODE/bootloader', env.BuildSubdir('bootloader'))
