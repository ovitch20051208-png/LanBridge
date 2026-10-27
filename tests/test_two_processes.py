import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("decline", [False, True])
def test_independent_peer_processes(tmp_path, decline):
    script = Path(__file__).resolve().parents[1] / "scripts/two_peer_demo.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(tmp_path), *(["--decline"] if decline else [])],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=25,
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(result.stdout.strip().splitlines()[-1])
    assert event["event"] == "passed" and event["processes"] == 2 and event["paired"]
    assert event["status"] == ("declined" if decline else "complete")
