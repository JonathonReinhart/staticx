from .pyinstaller import process_pyinstaller_archive
from .glibc import process_glibc_prog

hooks = [
    process_pyinstaller_archive,
    process_glibc_prog,
]


class HookContext:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def run_hooks(**kw):
    ctx = HookContext(**kw)
    for hook in hooks:
        hook(ctx)
