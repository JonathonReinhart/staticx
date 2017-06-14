import os

env = Environment(
    CCFLAGS = [
        '-std=gnu99',
        '-Wall', '-Werror',
        '-Wmissing-prototypes', '-Wstrict-prototypes',
    ],
    CPPPATH = ['#libtar'],

    BUILD_ROOT = '#scons_build',
    LIBDIR = '$BUILD_ROOT/lib',
    LIBPATH = '$LIBDIR'
)

env['CC'] = ARGUMENTS.get('CC') or os.environ.get('CC') or env['CC']

if ARGUMENTS.get('DEBUG'):
    env.Append(CPPDEFINES = {'DEBUG': 1})


libtar = env.SConscript(
    dirs = 'libtar',
    variant_dir = env.subst('$BUILD_ROOT/libtar'),
    duplicate = False,
    exports = dict(env=env.Clone()),
)
env.Install('$LIBDIR', libtar)

bl = env.SConscript(
    dirs = 'bootloader',
    variant_dir = env.subst('$BUILD_ROOT/bootloader'),
    duplicate = False,
    exports = dict(env=env.Clone()),
)
env.Install('#staticx', bl)
