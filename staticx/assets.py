import importlib.resources
import sys
from .utils import copy_fileobj_to_tempfile


def locate_asset(name, debug):
    mode = 'debug' if debug else 'release'
    path = '/'.join(('assets', mode, name))
    try:
        return importlib.resources.files("staticx").joinpath(path).open("rb")
    except FileNotFoundError:
        raise KeyError(f"Asset not found: {name!r} (mode={mode!r})")


def copy_asset_to_tempfile(assetname, debug, **kwargs):
    with locate_asset(assetname, debug) as fsrc:
        return copy_fileobj_to_tempfile(fsrc, **kwargs)
