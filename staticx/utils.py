import os
import errno
import shutil
from collections.abc import Iterable
from tempfile import NamedTemporaryFile
from .errors import *

def make_mode_executable(mode):
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    return mode


def make_executable(path):
    mode = os.stat(path).st_mode
    mode = make_mode_executable(mode)
    os.chmod(path, mode)

def get_symlink_target(path):
    dirpath = os.path.dirname(os.path.abspath(path))
    return os.path.join(dirpath, os.readlink(path))

def move_file(src, dst):
    if os.path.isdir(dst):
        raise DirectoryExistsError(dst)
    shutil.move(src, dst)


def mkdirs_for(filename):
    dirname = os.path.dirname(filename)
    os.makedirs(dirname, exist_ok=True)


def copy_to_tempfile(srcpath, **kwargs):
    with open(srcpath, 'rb') as fsrc:
        fdst = copy_fileobj_to_tempfile(fsrc, **kwargs)

    shutil.copystat(srcpath, fdst.name)
    return fdst


def copy_fileobj_to_tempfile(fsrc, **kwargs):
    fdst = NamedTemporaryFile(**kwargs)
    shutil.copyfileobj(fsrc, fdst)
    fdst.flush()
    fdst.seek(0)
    return fdst


def which_exec(name, env=None):
    for path in os.get_exec_path(env=env):
        xp = os.path.join(path, name)
        if os.access(xp, os.X_OK):
            return xp
    return None


def is_iterable(x):
    """Returns true if x is iterable but not a string"""
    return isinstance(x, Iterable) and not isinstance(x, str)

def coerce_sequence(x, t=list):
    if not is_iterable(x):
        x = [x]
    return t(x)

_SENTINEL = object()
_NO_DEFAULT = object()

def single(iterable, key=None, default=_NO_DEFAULT):
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

    result = _SENTINEL

    for i in iterable:
        if key(i):
            if result is not _SENTINEL:
                raise KeyError("Multiple items match key")
            result = i

    if result is not _SENTINEL:
        return result

    if default is not _NO_DEFAULT:
        return default

    raise KeyError("No items match key")
