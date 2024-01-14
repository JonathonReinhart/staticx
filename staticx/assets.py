import sys
from .utils import copy_fileobj_to_tempfile

# TODO(#265): Remove backport when Python 3.8 support is removed.
# importlib.resources.files() was added in Python 3.9.
if sys.version_info >= (3, 9):
    import importlib.resources as importlib_resources
else:
    import importlib_resources  # backport


def locate_asset(name, debug):
    mode = 'debug' if debug else 'release'
    path = '/'.join(('assets', mode, name))
    try:
        return importlib_resources.files("staticx").joinpath(path).open("rb")
    except FileNotFoundError:
        raise KeyError(f"Asset not found: {name!r} (mode={mode!r})")


def copy_asset_to_tempfile(assetname, debug, **kwargs):
    with locate_asset(assetname, debug) as fsrc:
        return copy_fileobj_to_tempfile(fsrc, **kwargs)
