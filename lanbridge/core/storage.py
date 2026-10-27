"""Small, atomic per-user state files; never store them in the source tree."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def _windows_sid() -> str:
    result = subprocess.run(
        ["whoami", "/user", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
        check=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return next(csv.reader([result.stdout.strip()]))[1]


def private_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("State directory must not be a symlink")
    if os.name == "nt":
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"*{_windows_sid()}:(OI)(CI)F"],
            capture_output=True,
            check=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    else:
        path.chmod(0o700)
    return path


def atomic_write(path: Path, data: bytes) -> None:
    fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if os.name != "nt":
            os.chmod(name, 0o600)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def write_json(path: Path, data: Any) -> None:
    atomic_write(path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))
