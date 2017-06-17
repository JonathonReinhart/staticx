from .pyinstaller import process_pyinstaller_archive

hooks = [
    process_pyinstaller_archive,
]

def run_hooks(ar, prog):
    for hook in hooks:
        hook(ar, prog)
