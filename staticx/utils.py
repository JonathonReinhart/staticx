import os
import errno
import shutil
from collections.abc import Callable, Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile
from tempfile import _TemporaryFileWrapper
from typing import cast, BinaryIO, TypeVar
from .errors import *


Pathlike = Path | str
T = TypeVar("T")

def make_mode_executable(mode: int) -> int:
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    return mode


def make_executable(path: Pathlike) -> None:
    mode = os.stat(path).st_mode
    mode = make_mode_executable(mode)
    os.chmod(path, mode)

def get_symlink_target(path: Pathlike) -> str:
    dirpath = os.path.dirname(os.path.abspath(path))
    return os.path.join(dirpath, os.readlink(path))

def move_file(src: Pathlike, dst: Pathlike) -> None:
    if os.path.isdir(dst):
        raise DirectoryExistsError(dst)
    shutil.move(src, dst)


def mkdirs_for(filename: Pathlike) -> None:
    dirname = os.path.dirname(filename)
    os.makedirs(dirname, exist_ok=True)


def copy_to_tempfile(srcpath: Pathlike, **kwargs) -> _TemporaryFileWrapper:
    with open(srcpath, 'rb') as fsrc:
        fdst = copy_fileobj_to_tempfile(fsrc, **kwargs)

    shutil.copystat(srcpath, fdst.name)
    return fdst


def copy_fileobj_to_tempfile(fsrc: BinaryIO, **kwargs) -> _TemporaryFileWrapper:
    fdst = NamedTemporaryFile(**kwargs)
    shutil.copyfileobj(fsrc, fdst)
    fdst.flush()
    fdst.seek(0)
    return fdst


def is_iterable(x: object) -> bool:
    """Returns true if x is iterable but not a string"""
    # TODO: Return typing.TypeGuard
    return isinstance(x, Iterable) and not isinstance(x, str)

def coerce_sequence(x: T | Iterable[T]) -> list[T]:
    if is_iterable(x):
        return list(cast(Iterable, x))
    return [cast(T, x)]

class _Sentinel:
    pass

_NO_DEFAULT = _Sentinel()

def single(
    iterable: Iterable[T],
    key: Callable[[T], bool] | None = None,
    default: T | None | _Sentinel = _NO_DEFAULT,
) -> T | None:
    """Returns a single item from iterable

    Arguments:
      iterable: Iterable sequence from which item is taken
      key:      Optional function to select item
      default:  Optional default value to return if no items match,
                otherwise KeyError is raised
    Returns:
      A single item from iterable matching key (if given)
    Raises:
      KeyError if multiple items in sequence match key
      KeyError if no items in sequence match key and default is not given
    """

    if key is None:
        key = lambda _: True

    result: T
    have_result = False

    for i in iterable:
        if key(i):
            if have_result:
                raise KeyError("Multiple items match key")
            result = i

    if have_result:
        return result

    if default is not _NO_DEFAULT:
        assert not isinstance(default, _Sentinel)
        return default

    raise KeyError("No items match key")
