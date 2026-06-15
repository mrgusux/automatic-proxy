"""Atomic file writer: write to temp then rename to avoid corruption."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: str | Path, content: str) -> None:
    """Write text atomically.

    Data is written to a temporary file in the same directory and then
    os.replace()'d into place. os.replace is atomic on POSIX and Windows, so a
    crash mid-write can never leave a half-written/corrupt output file.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, target)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def atomic_write_json(path: str | Path, data: Any) -> None:
    """Serialize ``data`` to JSON and write it atomically."""
    atomic_write_text(path, json.dumps(data, indent=2, ensure_ascii=False))
