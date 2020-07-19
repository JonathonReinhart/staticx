import pkg_resources
from .utils import copy_fileobj_to_tempfile

def locate_asset(name, debug):
    mode = 'debug' if debug else 'release'
    path = '/'.join(('assets', mode, name))
    try:
        return pkg_resources.resource_stream(__name__, path)
    except FileNotFoundError:
        raise KeyError("Asset not found: {!r} (mode={!r})".format(name, mode))


def copy_asset_to_tempfile(assetname, debug, **kwargs):
    with locate_asset(assetname, debug) as fsrc:
        return copy_fileobj_to_tempfile(fsrc, **kwargs)
