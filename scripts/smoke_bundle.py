"""Execute the frozen app outside its checkout and validate its diagnostic report."""

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve(strict=True)
    with tempfile.TemporaryDirectory(prefix="lanbridge-bundle-") as directory:
        report = Path(directory) / "report.json"
        env = {**os.environ, "QT_QPA_PLATFORM": "offscreen", "PYTHONPATH": "", "PYTHONHOME": ""}
        result = subprocess.run(
            [str(executable), "--self-test-report", str(report)],
            cwd=directory,
            env=env,
            capture_output=True,
            timeout=45,
        )
        if not report.exists():
            raise RuntimeError(f"Bundle diagnostics failed (exit {result.returncode}): {result.stderr!r}")
        data = json.loads(report.read_text(encoding="utf-8"))
        if (
            result.returncode
            or not data.get("frozen")
            or data.get("transfer") != "complete"
            or data.get("qt_dialog") != "passed"
        ):
            raise RuntimeError(f"Unexpected bundle report: {data}")
        print(json.dumps(data))


if __name__ == "__main__":
    main()
