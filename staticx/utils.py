import os
import errno
import shutil
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
    return fdst
