import tempfile
import os

from staticx import utils

def test_make_executable():
    with tempfile.NamedTemporaryFile() as tf:
        assert (os.stat(tf.name).st_mode & 0o111) == 0
        utils.make_executable(tf.name)
        assert (os.stat(tf.name).st_mode & 0o111) != 0
