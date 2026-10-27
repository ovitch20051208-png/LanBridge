"""Opt-in distribution diagnostics. No LAN listener or persistent state is used."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path

from lanbridge import __version__


async def _network(root: Path) -> dict:
    from lanbridge.core.identity import Identity, TrustStore
    from lanbridge.network.transfer import TransferServer, send_files

    left, right = Identity(root / "left"), Identity(root / "right")
    lt, rt = TrustStore(left.directory / "trust.json"), TrustStore(right.directory / "trust.json")
    lt.add(right.pem, "Self-test receiver")
    rt.add(left.pem, "Self-test sender")

    async def consent(*_):
        return True

    server = TransferServer(right, rt, root / "downloads", consent)
    port = await server.start()
    source = root / "打包 test.txt"
    source.write_text("LanBridge packaged TLS diagnostic\n", encoding="utf-8")
    try:
        status = await send_files(left, lt, right.id, "127.0.0.1", port, [source])
        result = (root / "downloads" / source.name).read_bytes()
        if result != source.read_bytes():
            raise RuntimeError("Packaged transfer content differs")
        return {"transfer": status, "sha256": hashlib.sha256(result).hexdigest()}
    finally:
        await server.close()


def run(report_path: Path) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import concurrent.futures

    from PySide6.QtCore import qVersion
    from PySide6.QtWidgets import QApplication

    from lanbridge.ui.app import DecisionDialog

    app = QApplication.instance() or QApplication([])
    future = concurrent.futures.Future()
    dialog = DecisionDialog("LanBridge self-test", "Test acceptance", future)
    dialog.accept()
    if not future.result():
        raise RuntimeError("Packaged Qt decision dialog failed")
    dialog.deleteLater()
    app.processEvents()
    with tempfile.TemporaryDirectory(prefix="lanbridge-selftest-") as directory:
        network = asyncio.run(_network(Path(directory)))
    report = {
        "ok": True,
        "version": __version__,
        "frozen": bool(getattr(sys, "frozen", False)),
        "platform": platform.system(),
        "architecture": platform.machine(),
        "qt": qVersion(),
        "qt_dialog": "passed",
        **network,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0
