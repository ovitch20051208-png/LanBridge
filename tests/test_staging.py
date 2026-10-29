import errno
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from lanbridge.core.storage import _windows_sid
from lanbridge.network import transfer


@pytest.mark.skipif(sys.platform != "win32", reason="Real Windows ACL and native mkdir required")
def test_native_acl_denial_is_bounded_and_tls_receiver_recovers(tmp_path):
    downloads = tmp_path / "received"
    downloads.mkdir()
    (downloads / "hello.txt").write_bytes(b"existing sentinel: must not change")
    sid = _windows_sid()
    script = Path(__file__).with_name("staging_receiver_probe.py")
    # No inherited/recursive deny; only this new directory and the actual test SID.
    subprocess.run(
        ["icacls", str(downloads), "/deny", f"*{sid}:(WD,AD)"], capture_output=True, check=True, timeout=5
    )
    try:
        try:
            result = subprocess.run(
                [sys.executable, str(script), str(tmp_path), sid],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=12,
            )
        except subprocess.TimeoutExpired as exc:
            pytest.fail(f"Native receiver blocked past 12 seconds; child terminated. Stack: {exc.stderr}")
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout.strip().splitlines()[-1])
        assert max(report["denied_seconds"]) < 2
        assert report["consents"] == 3 and report["recovery"] == "complete"
        print(json.dumps(report))
    finally:
        # Remove only the deny introduced above, even if the child was killed.
        subprocess.run(
            ["icacls", str(downloads), "/remove:d", f"*{sid}"],
            capture_output=True,
            check=True,
            timeout=5,
        )
        restored = downloads / "restored-probe"
        restored.mkdir()
        restored.rmdir()


def test_staging_collisions_preserve_existing_directory_and_file(tmp_path, monkeypatch):
    prefix = ".lanbridge-0123456789abcdef-"
    existing_directory = tmp_path / (prefix + "directory")
    existing_directory.mkdir()
    (existing_directory / "sentinel").write_bytes(b"keep")
    existing_file = tmp_path / (prefix + "file")
    existing_file.write_bytes(b"also keep")
    names = iter(["directory", "file", "fresh"])
    monkeypatch.setattr(transfer.secrets, "token_hex", lambda _: next(names))
    stage = transfer._create_staging(tmp_path, "0123456789abcdef" + "0" * 48)
    assert stage == tmp_path / (prefix + "fresh")
    assert stage.is_dir() and list(stage.iterdir()) == []
    assert (existing_directory / "sentinel").read_bytes() == b"keep"
    assert existing_file.read_bytes() == b"also keep"
    if os.name != "nt":
        assert stat.S_IMODE(stage.stat().st_mode) == 0o700


def test_staging_collision_retries_are_bounded(tmp_path, monkeypatch):
    def collide(*_args, **_kwargs):
        raise FileExistsError(errno.EEXIST, "Already exists")

    calls = []

    def name(_size):
        calls.append(1)
        return "collision"

    monkeypatch.setattr(transfer.secrets, "token_hex", name)
    monkeypatch.setattr(Path, "mkdir", collide)
    with pytest.raises(FileExistsError):
        transfer._create_staging(tmp_path, "0" * 64)
    assert len(calls) == 10


@pytest.mark.parametrize("error", [PermissionError(errno.EACCES, "Denied"), OSError(errno.ENOSPC, "Full")])
def test_staging_storage_errors_propagate_without_retry(tmp_path, monkeypatch, error):
    calls = []

    def fail(*_args, **_kwargs):
        calls.append(1)
        raise error

    monkeypatch.setattr(Path, "mkdir", fail)
    with pytest.raises(type(error)) as raised:
        transfer._create_staging(tmp_path, "0" * 64)
    assert raised.value is error and len(calls) == 1
