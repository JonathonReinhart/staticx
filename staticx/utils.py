import os
import errno
import shutil
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


def mkdir_p(path):
    # TODO Py2.7: Python 3 can simply use
    # os.makedirs(path, exist_ok=True)
    try:
        os.makedirs(path)
    except OSError as oe:
        if oe.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def mkdirs_for(filename):
    mkdir_p(os.path.dirname(filename))
