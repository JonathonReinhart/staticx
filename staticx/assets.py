import sys
from tempfile import _TemporaryFileWrapper
from typing import cast, Any, IO
from .utils import copy_fileobj_to_tempfile

# TODO(#265): Remove backport when Python 3.8 support is removed.
# importlib.resources.files() was added in Python 3.9.
if sys.version_info >= (3, 9):
    import importlib.resources as importlib_resources
else:
    import importlib_resources  # backport


def locate_asset(name: str, debug: bool) -> IO[bytes]:
    mode = 'debug' if debug else 'release'
    path = '/'.join(('assets', mode, name))
    try:
        file = importlib_resources.files("staticx").joinpath(path).open("rb")
        # For some reason, mypy --python-version=3.8 can't figure this out
        # even when importlib-resources is installed.
        # TODO(#265): Remove this cast when Python 3.8 support is removed.
        return cast(IO[bytes], file)
    except FileNotFoundError:
        raise KeyError(f"Asset not found: {name!r} (mode={mode!r})")


def copy_asset_to_tempfile(assetname: str, debug: bool, **kwargs: Any) -> _TemporaryFileWrapper:
    with locate_asset(assetname, debug) as fsrc:
        return copy_fileobj_to_tempfile(fsrc, **kwargs)
