import json
import subprocess
import sys


def test_diagnostic_entrypoint(tmp_path):
    report = tmp_path / "diagnostic.json"
    result = subprocess.run(
        [sys.executable, "-m", "lanbridge", "--self-test-report", str(report)],
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["ok"] and data["transfer"] == "complete" and data["qt_dialog"] == "passed"
    assert not data["frozen"]
