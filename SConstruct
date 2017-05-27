env = Environment(
    CCFLAGS = ['-Wall', '-Werror', '-fdiagnostics-color'],
    CPPPATH = ['#libtar'],

    BUILD_ROOT = '#build',
    LIBDIR = '#build/lib',
    LIBPATH = '$LIBDIR'
)

libtar = env.SConscript(
    dirs = 'libtar',
    variant_dir = env.subst('$BUILD_ROOT/libtar'),
    duplicate = False,
    exports = dict(env=env.Clone()),
)
env.Install('$LIBDIR', libtar)

env.SConscript(
    dirs = 'bootloader',
    variant_dir = env.subst('$BUILD_ROOT/bootloader'),
    duplicate = False,
    exports = dict(env=env.Clone()),
)
