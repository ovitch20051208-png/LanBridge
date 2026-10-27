"""Fail-fast milestone gate: lint, formatting and the full test suite."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    for arguments in (["ruff", "check", "."], ["ruff", "format", "--check", "."], ["pytest", "-q"]):
        subprocess.run([sys.executable, "-m", *arguments], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
