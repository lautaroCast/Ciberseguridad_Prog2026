"""Shared "does this filename stay inside output_dir" guard.

Used by both the write path (`report_generator.generate`) and the read
path (`routers.reports.download_report`) — previously each had its own
copy of this check, which is exactly the kind of duplication that lets
one side drift out of sync with the other (see the write side's `path.
parent != output_dir` — a plain `output_dir not in path.parents` check,
as both sides used to have, doesn't catch a `filename` like "abc/def.json":
it doesn't escape output_dir, so `.parents` matches it, but "abc/" was
never created, so *writing* it crashes with an unhandled FileNotFoundError.
`download_report` never hit this discrepancy because a missing "abc/"
correctly non-matches its file-exists check — but that was luck, not a
guarantee).
"""

import os
import uuid
from pathlib import Path


class PathEscapesOutputDirError(Exception):
    """Raised when `filename` would resolve outside (or not directly
    inside) `output_dir`."""


def resolve_within(output_dir: Path, filename: str) -> Path:
    output_dir = output_dir.resolve()
    candidate = (output_dir / filename).resolve()
    if candidate.parent != output_dir:
        raise PathEscapesOutputDirError(filename)
    return candidate


def atomic_write(path: Path, data: bytes) -> None:
    """Write `data` to `path` without ever exposing a partially-written
    file at that name.

    Writes to a sibling temp file in the same directory first (same
    filesystem, so the final `os.replace` is an atomic rename, not a
    copy) and only replaces `path` once the write is complete. Without
    this, a reader hitting `GET /reports/{id}/download` while a write to
    the same filename is still in progress (or interrupted mid-write)
    could see a truncated file instead of either the old or the new
    content.
    """
    tmp_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp_path.write_bytes(data)
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise
