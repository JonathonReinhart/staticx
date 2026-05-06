import io
import lzma
import tarfile
import tempfile
from unittest.mock import patch

import pytest

from staticx import archive
from staticx.constants import INTERP_FILENAME, PROG_FILENAME


def test_get_bcj_filter():
    with patch("staticx.archive.get_bcj_filter_arch") as mock_arch:
        mock_arch.return_value = "X86"
        filt = archive.get_bcj_filter()
        assert filt is not None
        assert filt.id == lzma.FILTER_X86
        assert filt.name == "FILTER_X86"

        mock_arch.return_value = None
        assert archive.get_bcj_filter() is None


def test_get_xz_filters():
    with patch("staticx.archive.get_bcj_filter") as mock_bcj:
        mock_bcj.return_value = archive.BcjFilter(id=lzma.FILTER_X86, name="FILTER_X86")
        filters = archive.get_xz_filters()
        assert len(filters) == 2
        assert filters[0]["id"] == lzma.FILTER_X86
        assert filters[1]["id"] == lzma.FILTER_LZMA2

        mock_bcj.return_value = None
        filters = archive.get_xz_filters()
        assert len(filters) == 1
        assert filters[0]["id"] == lzma.FILTER_LZMA2


def test_sxarchive_init_no_compress():
    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        assert sx.xzf is None
        assert sx.tar is not None
    assert not bio.closed


def test_sxarchive_init_compress():
    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=True) as sx:
        assert sx.xzf is not None
        assert sx.tar is not None
    assert not bio.closed


def test_sxarchive_add_symlink():
    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        sx.add_symlink("link", "target")

    bio.seek(0)
    with tarfile.open(fileobj=bio, mode="r") as tar:
        members = tar.getmembers()
        assert len(members) == 1
        assert members[0].issym()
        assert members[0].name == "link"
        assert members[0].linkname == "target"


def test_sxarchive_add_symlink_self_referential():
    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        with pytest.raises(
            ValueError, match="Refusing to add self-referential symlink"
        ):
            sx.add_symlink("foo", "foo")


def test_sxarchive_add_fileobj():
    bio = io.BytesIO()
    content = b"hello world"
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        with tempfile.NamedTemporaryFile() as tf:
            tf.write(content)
            tf.flush()
            tf.seek(0)
            sx.add_fileobj("test.txt", tf)

    bio.seek(0)
    with tarfile.open(fileobj=bio, mode="r") as tar:
        f = tar.extractfile("test.txt")
        assert f.read() == content


def test_sxarchive_add_program(tmp_path):
    prog = tmp_path / "myprog"
    prog.write_text("echo hello")
    prog.chmod(0o755)

    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        sx.add_program(prog, "myprog")

    bio.seek(0)
    with tarfile.open(fileobj=bio, mode="r") as tar:
        members = tar.getmembers()
        # Should have the program and a symlink
        assert len(members) == 2
        names = [m.name for m in members]
        assert "myprog" in names
        assert PROG_FILENAME in names

        prog_member = tar.getmember("myprog")
        assert prog_member.mode & 0o111 != 0

        link_member = tar.getmember(PROG_FILENAME)
        assert link_member.issym()
        assert link_member.linkname == "myprog"


def test_sxarchive_add_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("data")
    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        sx.add_file(f, arcname="archived_file.txt")

    bio.seek(0)
    with tarfile.open(fileobj=bio, mode="r") as tar:
        assert "archived_file.txt" in tar.getnames()


def test_sxarchive_add_interp_symlink():
    bio = io.BytesIO()
    with archive.SxArchive(bio, mode="w", compress=False) as sx:
        sx.add_interp_symlink("/lib/ld-linux.so.2")

    bio.seek(0)
    with tarfile.open(fileobj=bio, mode="r") as tar:
        member = tar.getmember(INTERP_FILENAME)
        assert member.issym()
        assert member.linkname == "ld-linux.so.2"
