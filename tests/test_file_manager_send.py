from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QLabel, QMessageBox, QPushButton

from lanbridge.core.config import Settings
from lanbridge.network.discovery import Peer
from lanbridge.ui.app import MainWindow
from lanbridge.ui.worker import Events, NetworkWorker


def make_window(qapp, tmp_path, monkeypatch, *, ready=True):
    events = Events()
    worker = NetworkWorker(Settings.load(tmp_path / "state"), events, port=0, discovery=False)
    window = MainWindow(worker.settings, worker, events)
    calls = []
    monkeypatch.setattr(worker, "send", lambda peer, paths: calls.append((peer.id, list(paths))))
    monkeypatch.setattr(window.tray, "showMessage", lambda *args: None)
    if ready:
        events.ready.emit(1234)
    return window, worker, calls


def dispose(window):
    for dialog in list(window.dialogs):
        dialog.reject()
    window.tray.hide()
    window.hide()
    window.deleteLater()


def test_right_click_sends_to_only_paired_online_device_without_showing_main(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    paired = Peer("a" * 64, "Mac", "Darwin", "127.0.0.1", 1234)
    stranger = Peer("b" * 64, "Unpaired", "Windows", "127.0.0.1", 1235)
    worker.trust.peers[paired.id] = {"name": paired.name}
    window.set_peers([stranger, paired])
    paths = [tmp_path / "中文 file.txt"]
    try:
        window.send_from_file_manager(paths)
        assert calls == [(paired.id, paths)]
        assert not window.isVisible() and not window.dialogs
        window.set_files(paths)
        assert len(calls) == 1  # Ordinary file selection still requires Send files.
    finally:
        dispose(window)


def test_multiple_recipients_need_one_click_and_keep_separate_requests(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    peers = [Peer(c * 64, c, "Desktop", "127.0.0.1", 1234) for c in "ab"]
    worker.trust.peers.update({peer.id: {"name": peer.name} for peer in peers})
    window.set_peers(peers)
    first, second = [tmp_path / "first.txt"], [tmp_path / "second.txt"]
    try:
        window.send_from_file_manager(first)
        window.send_from_file_manager(second)
        assert not calls
        picker = window.file_manager_picker
        picker.devices.itemClicked.emit(picker.devices.item(1))
        picker.devices.itemActivated.emit(picker.devices.item(1))
        qapp.processEvents()
        assert calls == [(peers[1].id, first)]
        picker = window.file_manager_picker
        picker.devices.itemClicked.emit(picker.devices.item(0))
        qapp.processEvents()
        assert calls == [(peers[1].id, first), (peers[0].id, second)]
    finally:
        dispose(window)


def test_unpaired_or_offline_devices_cannot_receive_right_click_send(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    worker.trust.peers["a" * 64] = {"name": "Offline"}
    window.set_peers([Peer("b" * 64, "Unpaired", "Desktop", "127.0.0.1", 1234)])
    try:
        window.send_from_file_manager([tmp_path / "test.txt"])
        assert window.file_manager_picker.devices.count() == 0
        window.file_manager_picker.reject()
        qapp.processEvents()
        assert not calls
    finally:
        dispose(window)


def test_right_click_waits_for_startup_and_uses_current_discovery(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch, ready=False)
    peer = Peer("a" * 64, "Mac", "Darwin", "127.0.0.1", 1234)
    worker.trust.peers[peer.id] = {"name": peer.name}
    paths = [tmp_path / "test.txt"]
    try:
        window.send_from_file_manager(paths)
        assert not calls
        window.set_peers([peer])
        worker.events.ready.emit(1234)
        assert calls == [(peer.id, paths)]
    finally:
        dispose(window)


def test_revoked_recipient_cannot_be_sent_from_stale_picker(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    peers = [Peer(c * 64, c, "Desktop", "127.0.0.1", 1234) for c in "ab"]
    worker.trust.peers.update({peer.id: {"name": peer.name} for peer in peers})
    window.set_peers(peers)
    try:
        window.send_from_file_manager([tmp_path / "test.txt"])
        worker.trust.peers.clear()
        picker = window.file_manager_picker
        picker.devices.itemClicked.emit(picker.devices.item(0))
        assert not calls and picker.isVisible()
    finally:
        dispose(window)


def test_empty_file_action_never_sends_previous_selection(qapp, tmp_path, monkeypatch):
    window, _, calls = make_window(qapp, tmp_path, monkeypatch)
    try:
        window.set_files([tmp_path / "previous.txt"])
        window.hide()
        window.send_from_file_manager([])
        assert not calls and window.isVisible()
    finally:
        dispose(window)


def test_reopening_existing_app_preserves_selection_and_does_not_send(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    paths = [tmp_path / "previous selection.txt"]
    try:
        window.set_files(paths)
        window.hide()
        worker.events.forwarded.emit([])
        assert window.isVisible() and window.paths == paths
        assert not calls
    finally:
        dispose(window)


def test_removing_mistaken_files_sends_only_remaining_paths_and_keeps_originals(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    peer = Peer("a" * 64, "Receiver", "Desktop", "127.0.0.1", 1234)
    worker.trust.peers[peer.id] = {"name": peer.name}
    window.set_peers([peer])
    window.device_list.setCurrentRow(0)
    paths = [tmp_path / "first" / "same.txt", tmp_path / "second" / "same.txt", tmp_path / "中文 文件.txt"]
    for index, path in enumerate(paths):
        path.parent.mkdir(exist_ok=True)
        path.write_text(str(index))
    try:
        window.set_files(paths)
        window.files_list.item(1).setSelected(True)
        window.remove_files_button.click()
        window.send_button.click()
        assert calls == [(peer.id, [paths[0], paths[2]])]
        assert [path.read_text() for path in paths] == ["0", "1", "2"]
        window.files_list.item(0).setSelected(True)
        window.files_list.item(1).setSelected(True)
        window.remove_files_button.click()
        assert not window.paths and not window.send_button.isEnabled()
        assert not window.clear_files_button.isEnabled() and not window.remove_files_button.isEnabled()
        assert window.files_list.isHidden() and "Choose files" in window.files_label.text()
    finally:
        dispose(window)


def test_focused_delete_and_clear_list_do_not_change_an_already_started_send(qapp, tmp_path, monkeypatch):
    window, worker, calls = make_window(qapp, tmp_path, monkeypatch)
    peer = Peer("a" * 64, "Receiver", "Desktop", "127.0.0.1", 1234)
    worker.trust.peers[peer.id] = {"name": peer.name}
    window.set_peers([peer])
    window.device_list.setCurrentRow(0)
    paths = [tmp_path / "keep.txt", tmp_path / "remove.txt"]
    try:
        window.set_files(paths)
        window.send_button.click()
        window.files_list.setCurrentRow(1)
        window.files_list.setFocus()
        qapp.processEvents()
        QTest.keyClick(window.files_list, Qt.Key.Key_Delete)
        assert window.paths == [paths[0]]
        window.clear_files_button.click()
        assert not window.paths and not window.send_button.isEnabled()
        assert calls == [(peer.id, paths)]  # The started send owns an independent snapshot.
        window.open_request([])
        assert not window.paths and not window.send_button.isEnabled()
    finally:
        dispose(window)


def test_install_status_refreshes_and_reinstall_updates_same_action(qapp, tmp_path, monkeypatch):
    from lanbridge.platform import integration

    window, _, _ = make_window(qapp, tmp_path, monkeypatch)
    path = tmp_path / "action"
    monkeypatch.setattr(integration, "action_path", lambda: path)
    monkeypatch.setattr(integration, "install", lambda: (path.write_text("shortcut"), path)[1])
    monkeypatch.setattr(integration, "uninstall", lambda: path.unlink())
    monkeypatch.setattr(QMessageBox, "information", lambda *args: None)
    try:
        window.show_settings()
        dialog = window.dialogs[-1]
        buttons = dialog.findChildren(QPushButton)
        install = next(button for button in buttons if button.text() == "Install file-manager action")
        remove = next(button for button in buttons if button.text() == "Remove action")
        assert not remove.isEnabled()
        install.click()
        assert install.text() == "Reinstall file-manager action" and remove.isEnabled()
        install.click()
        assert path.read_text() == "shortcut" and len(list(tmp_path.glob("action"))) == 1
        assert any("File-manager action: Installed" in label.text() for label in dialog.findChildren(QLabel))
        remove.click()
        assert not path.exists() and not remove.isEnabled()
        assert install.text() == "Install file-manager action"
    finally:
        dispose(window)
