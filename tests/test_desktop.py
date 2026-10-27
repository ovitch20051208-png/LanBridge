import asyncio
import concurrent.futures
import socket

import pytest
from PySide6.QtWidgets import QApplication, QDialog
from zeroconf import ServiceInfo

from lanbridge.core.config import Settings
from lanbridge.network.discovery import SERVICE, Peer, parse_peer
from lanbridge.ui.app import DecisionDialog, MainWindow, human_size
from lanbridge.ui.worker import Events, NetworkWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


def test_discovery_metadata():
    info = ServiceInfo(
        SERVICE,
        "test." + SERVICE,
        addresses=[socket.inet_aton("192.168.1.3")],
        port=47384,
        properties={"v": "1", "id": "a" * 64, "name": "Mac 你好", "os": "Darwin", "pair_port": "1234"},
    )
    peer = parse_peer(info)
    assert peer.id == "a" * 64 and peer.name == "Mac 你好" and peer.pair_port == 1234
    info.properties[b"v"] = b"99"
    with pytest.raises(ValueError):
        parse_peer(info)


def test_accept_decline_dialog(qapp):
    for accept in (True, False):
        future = concurrent.futures.Future()
        dialog = DecisionDialog("Test", "Incoming file", future)
        dialog.accept() if accept else dialog.reject()
        assert future.result() == accept
        dialog.deleteLater()


def test_dialog_timeout(qapp):
    future = concurrent.futures.Future()
    dialog = DecisionDialog("Test", "file", future, timeout=-1)
    dialog._check()
    assert future.result() is False
    assert dialog.result() == QDialog.DialogCode.Rejected


def test_window_selection_and_tray(qapp, tmp_path):
    settings = Settings.load(tmp_path / "state")
    events = Events()
    worker = NetworkWorker(settings, events, port=0, discovery=False)
    window = MainWindow(settings, worker, events)
    peer = Peer("b" * 64, "Mac", "Darwin", "127.0.0.1", 9999)
    window.set_peers([peer, peer])
    assert len(window.peers) == 1
    assert window.device_list.count() == 1
    window.device_list.setCurrentRow(0)
    assert window.pair_button.isEnabled()
    assert not window.send_button.isEnabled()
    assert [a.text() for a in window.tray_menu.actions()] == [
        "Open LanBridge",
        "Nearby Devices",
        "Received Files",
        "Settings",
        "Quit",
    ]
    window.tray.hide()
    window.hide()
    window.deleteLater()


def test_human_sizes():
    assert human_size(1024) == "1.0 KiB"


async def test_desktop_background_receiver_with_real_tls(qapp, peers, tmp_path):
    from lanbridge.network.transfer import send_files

    a, at, _, _ = peers
    settings = Settings.load(tmp_path / "desktop")
    settings.downloads = tmp_path / "received"
    events = Events()
    worker = NetworkWorker(settings, events, port=0, discovery=False)
    at.add(worker.identity.pem, "Desktop")
    worker.trust.add(a.pem, "Sender")
    window = MainWindow(settings, worker, events)
    ready = []
    events.ready.connect(ready.append)
    worker.start()
    try:
        for _ in range(300):
            qapp.processEvents()
            if ready:
                break
            await asyncio.sleep(0.01)
        assert ready
        source = tmp_path / "desktop.txt"
        source.write_text("Qt consent over real TLS")
        sending = asyncio.create_task(send_files(a, at, worker.identity.id, "127.0.0.1", ready[0], [source]))
        for _ in range(300):
            qapp.processEvents()
            for dialog in list(window.dialogs):
                if isinstance(dialog, DecisionDialog):
                    dialog.accept()
            if sending.done():
                break
            await asyncio.sleep(0.01)
        assert await asyncio.wait_for(sending, 2) == "complete"
        assert (settings.downloads / "desktop.txt").read_text() == "Qt consent over real TLS"
    finally:
        worker.stop()
        window.tray.hide()
        window.hide()
        window.deleteLater()
