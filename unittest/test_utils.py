import tempfile
import os
import pytest
import subprocess

from staticx import utils

def test_make_executable():
    with tempfile.NamedTemporaryFile() as tf:
        assert (os.stat(tf.name).st_mode & 0o111) == 0
        utils.make_executable(tf.name)
        assert (os.stat(tf.name).st_mode & 0o111) != 0

# is_iterable
def test_is_iterable_str():
    assert not utils.is_iterable("foo")

def test_is_iterable_list():
    assert utils.is_iterable([1, 2, 3])

def test_is_iterable_tuple():
    assert utils.is_iterable((1, 2, 3))


# coerce_sequence
def test_coerce_sequence_scalar_input():
    assert utils.coerce_sequence(42) == [42]
    assert utils.coerce_sequence("foo") == ["foo"]

def test_coerce_sequence_list_input():
    assert utils.coerce_sequence([69, 420]) == [69, 420]
    assert utils.coerce_sequence(["foo", "bar"]) == ["foo", "bar"]

def test_coerce_sequence_tuple_input():
    assert utils.coerce_sequence((69, 420)) == [69, 420]
    assert utils.coerce_sequence(("foo", "bar")) == ["foo", "bar"]

def test_coerce_sequence_tuple_output():
    assert utils.coerce_sequence([69, 420], tuple) == (69, 420)


# single
def test_single_success():
    assert utils.single(['ok']) == 'ok'

def test_single_empty():
    with pytest.raises(KeyError, match='No items match key'):
        utils.single([])

def test_single_multiple():
    with pytest.raises(KeyError, match='Multiple items match key'):
        utils.single(['a', 'b'])

def test_single_key_none():
    with pytest.raises(KeyError, match='No items match key'):
        utils.single([1, 2, 3], key=lambda x: x<0)

def test_single_key_multiple():
    with pytest.raises(KeyError, match='Multiple items match key'):
        utils.single([1, 2, 3], key=lambda x: x>0)

def test_single_empty_default():
    assert utils.single([], default='ok') == 'ok'

def test_single_key_none_default():
    assert utils.single([1, 2, 3], key=lambda x: x<0, default='ok') == 'ok'

# which_exec
def test_which_exec_common():
    def ext_which(name):
        return subprocess.check_output(['which', name]).decode().strip()

    for name in ('true', 'date', 'bash', 'python3'):
        assert ext_which(name) == utils.which_exec(name)

def test_which_exec_bogus():
    assert utils.which_exec('zZzZzZzZzZzZzZz') == None
