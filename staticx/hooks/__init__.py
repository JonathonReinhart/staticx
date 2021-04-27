from .pyinstaller import process_pyinstaller_archive
from .glibc import process_glibc_prog

hooks = [
    process_pyinstaller_archive,
    process_glibc_prog,
]


def run_hooks(sx):
    for hook in hooks:
        hook(sx)
