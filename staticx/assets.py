import importlib.resources
from tempfile import _TemporaryFileWrapper
from typing import IO, Any
import shutil

from .utils import copy_fileobj_to_tempfile


def locate_asset(name: str, debug: bool) -> IO[bytes]:
    mode = "debug" if debug else "release"
    path = f"assets/{mode}/{name}"
    try:
        path = importlib_resources.files("staticx").joinpath(path)
        fpath = path.open("rb")
        return (path,fpath)
    except FileNotFoundError:
        raise KeyError(f"Asset not found: {name!r} (mode={mode!r})")


def copy_asset_to_tempfile(
    assetname: str, debug: bool, **kwargs: Any
) -> _TemporaryFileWrapper:
    asset = locate_asset(assetname, debug)
    with asset[1] as fsrc:
        fdst = copy_fileobj_to_tempfile(fsrc, **kwargs)
        shutil.copystat(asset[0], fdst.name)
        return fdst
