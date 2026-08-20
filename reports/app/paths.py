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
