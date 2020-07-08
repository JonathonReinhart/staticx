import os

# Set up base environment
base_env = Environment(
    CCFLAGS = [
        '-std=gnu99',
        '-Wall', '-Werror',
        '-Wmissing-prototypes', '-Wstrict-prototypes',
    ],
    CPPPATH = [
        '#libtar',
        '#libxz',
    ],

    BUILD_ROOT = '#scons_build',
    BUILD_DIR = '$BUILD_ROOT/$MODE',
    LIBDIR = '$BUILD_DIR/lib',
    LIBPATH = '$LIBDIR'
)

base_env['CC'] = ARGUMENTS.get('CC') or os.environ.get('CC') or base_env['CC']

# Setup Release environment
release_env = base_env.Clone(
    MODE = 'release',
)
release_env.Append(
    CPPDEFINES = {'NDEBUG': 1},
    CPPFLAGS = ['-Os'],
)

# Setup Debug environment
debug_env = base_env.Clone(
    MODE = 'debug',
)
debug_env.Append(
    CPPDEFINES = {'DEBUG': 1},
    CPPFLAGS = ['-g'],
)


# Build in all environments
for env in (release_env, debug_env):
    libtar = env.SConscript(
        dirs = 'libtar',
        variant_dir = '$BUILD_DIR/libtar',
        duplicate = False,
        exports = dict(env=env.Clone()),
    )
    env.Install('$LIBDIR', libtar)

    libxz = env.SConscript(
        dirs = 'libxz',
        variant_dir = '$BUILD_DIR/libxz',
        duplicate = False,
        exports = dict(env=env.Clone()),
    )
    env.Install('$LIBDIR', libxz)

    bl = env.SConscript(
        dirs = 'bootloader',
        variant_dir = '$BUILD_DIR/bootloader',
        duplicate = False,
        exports = dict(env=env.Clone()),
    )
    env.InstallAs('#staticx/assets/$MODE/bootloader', bl)
