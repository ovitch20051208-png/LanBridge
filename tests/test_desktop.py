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


def test_progress_selects_correct_transfer_for_cancel(qapp, tmp_path):
    from lanbridge.network.transfer import Progress

    settings = Settings.load(tmp_path / "progress-state")
    events = Events()
    worker = NetworkWorker(settings, events, discovery=False)
    window = MainWindow(settings, worker, events)
    window.update_progress(Progress("first", "send", 5, 100, 10, "transferring"))
    window.update_progress(Progress("second", "receive", 0, 200, 0, "waiting"))
    window.transfer_selector.setCurrentIndex(0)
    assert window.active_id == "first" and window.progress.value() == 5
    window.update_progress(Progress("second", "receive", 200, 200, 20, "complete"))
    assert window.active_id == "first" and window.cancel_button.isEnabled()
    window.tray.hide()
    window.deleteLater()


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


async def test_two_desktops_pair_and_receive_while_hidden(qapp, tmp_path, monkeypatch):
    import re

    from PySide6.QtWidgets import QSystemTrayIcon

    left_settings = Settings.load(tmp_path / "left-desktop")
    right_settings = Settings.load(tmp_path / "right-desktop")
    right_settings.downloads = tmp_path / "desktop-downloads"
    left_events, right_events = Events(), Events()
    left = NetworkWorker(left_settings, left_events, port=0, discovery=False)
    right = NetworkWorker(right_settings, right_events, port=0, discovery=False)
    left_window = MainWindow(left_settings, left, left_events)
    right_window = MainWindow(right_settings, right, right_events)
    left_ready, right_ready = [], []
    left_events.ready.connect(left_ready.append)
    right_events.ready.connect(right_ready.append)
    left.start()
    right.start()

    async def until(predicate):
        for _ in range(500):
            qapp.processEvents()
            if predicate():
                return
            await asyncio.sleep(0.01)
        raise AssertionError("Desktop workflow timed out")

    try:
        await until(lambda: left_ready and right_ready)
        right.allow_pairing()
        pairing = left.pair_address("127.0.0.1", right.pair_port)
        await until(lambda: left_window.dialogs and right_window.dialogs)
        codes = []
        for window in (left_window, right_window):
            dialog = window.dialogs[0]
            codes.append(re.search(r"[A-F0-9]{4}(?: [A-F0-9]{4}){5}", dialog.text.text()).group())
        assert codes[0] == codes[1]
        for window in (left_window, right_window):
            window.dialogs[0].accept()
        await until(pairing.done)
        assert left.identity.id in right.trust.peers and right.identity.id in left.trust.peers
        monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: True)
        right_window.show()
        right_window.close()
        assert not right_window.isVisible() and right.thread.is_alive()
        source = tmp_path / "hidden recipient.txt"
        source.write_text("Receiver main window stays hidden")
        sending = left.send(Peer(right.identity.id, "Receiver", "Desktop", "127.0.0.1", right.port), [source])
        await until(lambda: right_window.dialogs)
        right_window.dialogs[0].accept()
        await until(sending.done)
        assert (right_settings.downloads / source.name).read_text() == source.read_text()
        assert not right_window.isVisible()
    finally:
        left.stop()
        right.stop()
        for window in (left_window, right_window):
            window.tray.hide()
            window.hide()
            window.deleteLater()
