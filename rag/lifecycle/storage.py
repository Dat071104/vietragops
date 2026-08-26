"""Atomic local file writes.

Every lifecycle write (candidate artifacts, live manifest/chunks) goes through
`write_bytes_atomic`: content is written to a temp file in the same directory,
then moved into place with `os.replace`, which is atomic on both POSIX and
NTFS. A concurrent reader therefore always sees either the fully old file or
the fully new one -- never a partial write.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def write_bytes_atomic(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".tmp_{path.name}_")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
