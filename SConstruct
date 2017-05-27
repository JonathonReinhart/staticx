env = Environment(
    CCFLAGS = ['-Wall', '-Werror', '-fdiagnostics-color'],
    BUILD_ROOT = '#build',
)

env.SConscript(
    dirs = 'bootloader',
    variant_dir = env.subst('$BUILD_ROOT/bootloader'),
    duplicate = False,
    exports = dict(env=env.Clone()),
)
