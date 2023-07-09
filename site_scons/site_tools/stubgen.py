from SCons.Util import is_List

def ShlibStubGen(env, target, symbols):
    """Generate a shared library stub

    This stub is used to facilitate dynamic linking without including
    occasionally problematic symbol versioning information.

    Parameters:
        env:        Environment
        target:     Target shared object name (e.g. libc.so.6)
        symbols:    Symbol list to include in stub
    """
    # Inspired by https://stackoverflow.com/a/21059674

    if is_List(target):
        raise UserError("target must be a single string or node")
    target = env.fs.File(target)

    lines = ['// Auto-generated stub']
    for sym in symbols:
        lines += [
            f'void {sym}(void);',       # for strict prototypes
            f'void {sym}(void) {{}}',
            '',
        ]

    csrc = env.Textfile(
        target = target.name + '_stub.c',
        source = lines,
    )

    stub = env.SharedLibrary(
        target = target,
        source = [csrc],
        CCFLAGS = env['CCFLAGS'] + [
            '-fno-builtin',
        ],
        LINKFLAGS = env['LINKFLAGS'] + [
            '-Wl,-soname=${TARGET.name}',
            '-nostdlib',
        ],
        SHLIBSUFFIX='',
    )
    return stub


def generate(env):
    env.Tool('textfile')
    env.AddMethod(ShlibStubGen)

def exists(env):
    return True
