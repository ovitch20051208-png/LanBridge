from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
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
    parser.add_argument("--install-integration", action="store_true")
    parser.add_argument("--uninstall-integration", action="store_true")
    parser.add_argument(
        "--self-test-report", type=Path, help="Run isolated loopback/Qt diagnostics and write JSON"
    )
    args = parser.parse_args()
    if args.self_test_report:
        from lanbridge.selftest import run

        return run(args.self_test_report)
    if args.install_integration or args.uninstall_integration:
        from lanbridge.platform import integration

        if args.install_integration:
            print(integration.install())
        else:
            integration.uninstall()
        return 0
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.StreamHandler()] if sys.stderr else [],
    )
    from PySide6.QtWidgets import QApplication

    from lanbridge.core.config import Settings
    from lanbridge.ipc.instance import SingleInstance
    from lanbridge.ui.app import MainWindow
    from lanbridge.ui.worker import Events, NetworkWorker

    app = QApplication(sys.argv[:1])
    app.setApplicationName("LanBridge")
    app.setOrganizationName("LanBridge")
    app.setQuitOnLastWindowClosed(False)
    settings = Settings.load(args.data_dir)
    file_log = RotatingFileHandler(
        settings.directory / "lanbridge.log", maxBytes=2 * 1024**2, backupCount=2, encoding="utf-8"
    )
    file_log.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(file_log)
    events = Events()
    instance = SingleInstance(settings.directory, events.forwarded.emit)
    if not instance.acquire():
        if instance.forward(args.files):
            return 0
        logging.error("LanBridge is already running, but its local IPC did not respond")
        return 1
    app.aboutToQuit.connect(instance.close)
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
