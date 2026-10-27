from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="LanBridge local desktop file transfer")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--send", action="store_true", help="Show recipient selection for supplied files")
    parser.add_argument("--data-dir", type=Path, help="Isolated state directory for testing")
    parser.add_argument("--port", type=int, default=47384)
    parser.add_argument("--no-discovery", action="store_true")
    parser.add_argument("--background", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    from PySide6.QtWidgets import QApplication

    from lanbridge.core.config import Settings
    from lanbridge.ui.app import MainWindow
    from lanbridge.ui.worker import Events, NetworkWorker

    app = QApplication(sys.argv[:1])
    app.setApplicationName("LanBridge")
    app.setOrganizationName("LanBridge")
    app.setQuitOnLastWindowClosed(False)
    settings = Settings.load(args.data_dir)
    events = Events()
    worker = NetworkWorker(settings, events, port=args.port, discovery=not args.no_discovery)
    window = MainWindow(settings, worker, events)
    app.aboutToQuit.connect(worker.stop)
    worker.start()
    if args.files:
        window.set_files(args.files)
    elif not args.background:
        window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
