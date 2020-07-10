from .pyinstaller import process_pyinstaller_archive

hooks = [
    process_pyinstaller_archive,
]


class HookContext:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def run_hooks(**kw):
    ctx = HookContext(**kw)
    for hook in hooks:
        hook(ctx)
