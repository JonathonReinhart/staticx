import os
import tempfile

import pytest

from staticx import utils


def test_make_mode_executable():
    assert utils.make_mode_executable(0o444) == 0o555
    assert utils.make_mode_executable(0o644) == 0o755
    assert utils.make_mode_executable(0o600) == 0o700
    assert utils.make_mode_executable(0o755) == 0o755


def test_make_executable():
    with tempfile.NamedTemporaryFile() as tf:
        os.chmod(tf.name, 0o644)
        assert (os.stat(tf.name).st_mode & 0o111) == 0
        utils.make_executable(tf.name)
        assert (os.stat(tf.name).st_mode & 0o111) != 0


def test_get_symlink_target(tmp_path):
    target = tmp_path / "target"
    target.write_text("hello")
    link = tmp_path / "link"
    os.symlink(target, link)
    assert utils.get_symlink_target(link) == str(target)


def test_move_file(tmp_path):
    src = tmp_path / "src"
    src.write_text("hello")
    dst = tmp_path / "dst"
    utils.move_file(str(src), str(dst))
    assert dst.read_text() == "hello"
    assert not src.exists()


def test_move_file_directory_exists_error(tmp_path):
    src = tmp_path / "src"
    src.write_text("hello")
    dst = tmp_path / "dst_dir"
    dst.mkdir()
    from staticx.errors import DirectoryExistsError

    with pytest.raises(DirectoryExistsError):
        utils.move_file(str(src), str(dst))


def test_mkdirs_for(tmp_path):
    path = tmp_path / "a" / "b" / "c.txt"
    utils.mkdirs_for(path)
    assert (tmp_path / "a" / "b").is_dir()


def test_copy_fileobj_to_tempfile():
    content = b"hello world"
    with tempfile.TemporaryFile() as fsrc:
        fsrc.write(content)
        fsrc.seek(0)
        with utils.copy_fileobj_to_tempfile(fsrc) as tf:
            assert tf.read() == content


def test_copy_to_tempfile(tmp_path):
    src = tmp_path / "test.txt"
    content = b"hello world"
    src.write_bytes(content)
    os.chmod(src, 0o755)

    with utils.copy_to_tempfile(src) as tf:
        assert tf.read() == content
        assert (os.stat(tf.name).st_mode & 0o777) == 0o755


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


# single
def test_single_success():
    assert utils.single(["ok"]) == "ok"


def test_single_empty():
    with pytest.raises(KeyError, match="No items match key"):
        utils.single([])


def test_single_multiple():
    with pytest.raises(KeyError, match="Multiple items match key"):
        utils.single(["a", "b"])


def test_single_key_none():
    with pytest.raises(KeyError, match="No items match key"):
        utils.single([1, 2, 3], key=lambda x: x < 0)


def test_single_key_multiple():
    with pytest.raises(KeyError, match="Multiple items match key"):
        utils.single([1, 2, 3], key=lambda x: x > 0)


def test_single_empty_default():
    assert utils.single([], default="ok") == "ok"


def test_single_key_none_default():
    assert utils.single([1, 2, 3], key=lambda x: x < 0, default="ok") == "ok"
