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


def mkdirs_for(filename):
    dirname = os.path.dirname(filename)
    os.makedirs(dirname, exist_ok=True)
