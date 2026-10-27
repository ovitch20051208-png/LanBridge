"""PyInstaller entry point (absolute import, safe outside the source checkout)."""

import json
import sys
import traceback
from pathlib import Path

from lanbridge.__main__ import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        details = traceback.format_exc()
        if "--self-test-report" in sys.argv:
            target = Path(sys.argv[sys.argv.index("--self-test-report") + 1])
            target.write_text(json.dumps({"ok": False, "error": details}), encoding="utf-8")
        else:
            from platformdirs import user_log_path
            from PySide6.QtWidgets import QApplication, QMessageBox

            directory = user_log_path("LanBridge", appauthor=False)
            directory.mkdir(parents=True, exist_ok=True)
            log = directory / "startup-error.log"
            log.write_text(details, encoding="utf-8")
            app = QApplication.instance() or QApplication([])
            QMessageBox.critical(
                None, "LanBridge could not start", f"Startup failed. Diagnostics were saved to {log}"
            )
        raise SystemExit(1) from None
