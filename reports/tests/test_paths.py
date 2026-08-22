from pathlib import Path

import pytest

from app.paths import atomic_write


def test_atomic_write_creates_file_with_expected_content(tmp_path: Path):
    target = tmp_path / "report.json"
    atomic_write(target, b'{"ok": true}')

    assert target.read_bytes() == b'{"ok": true}'
    assert list(tmp_path.iterdir()) == [target]


def test_atomic_write_replaces_existing_file(tmp_path: Path):
    target = tmp_path / "report.json"
    target.write_bytes(b"old content")

    atomic_write(target, b"new content")

    assert target.read_bytes() == b"new content"
    assert list(tmp_path.iterdir()) == [target]


def test_atomic_write_leaves_no_tmp_file_and_preserves_original_on_failure(
    tmp_path: Path, monkeypatch
):
    target = tmp_path / "report.json"
    target.write_bytes(b"original content")

    def _boom(self, data):
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_bytes", _boom)

    with pytest.raises(OSError):
        atomic_write(target, b"new content")

    # the original file must survive untouched, and no leftover .tmp file
    assert target.read_bytes() == b"original content"
    assert list(tmp_path.iterdir()) == [target]
