import asyncio

import pytest

from lanbridge.core.config import Settings
from lanbridge.core.protocol import ProtocolError, TransferCancelled
from lanbridge.network.discovery import Peer
from lanbridge.network.transfer import Progress
from lanbridge.ui.app import MainWindow
from lanbridge.ui.worker import Events, NetworkWorker


@pytest.fixture
def desktop(qapp, tmp_path, monkeypatch):
    events = Events()
    worker = NetworkWorker(Settings.load(tmp_path / "state"), events, port=0, discovery=False)
    window = MainWindow(worker.settings, worker, events)
    monkeypatch.setattr(window.tray, "showMessage", lambda *args: None)
    events.ready.emit(1234)
    yield window, worker
    window.tray.hide()
    window.hide()
    window.deleteLater()
    worker.loop.close()


def test_failed_percent_is_replaced_and_archiving_retains_reviewable_history(desktop):
    window, _ = desktop
    failed = Progress("failed", "send", 32, 100, 0, "error: Connection lost")
    window.update_progress(failed)
    assert window.progress.format() == "Failed" and window.progress.value() == 0
    assert "32.0 B transferred" in window.status.text()
    assert not window.cancel_button.isEnabled() and window.archive_button.isEnabled()
    window.archive_button.click()
    assert window.progress.isHidden() and window.active_id is None
    assert window.status.text().startswith("Ready to receive")
    assert window.transfers[failed.id] == failed
    assert window.transfer_selector.itemText(0).startswith("Archived ·")
    window.transfer_selector.setCurrentIndex(0)
    assert "Connection lost" in window.status.text()
    window.archive_button.click()
    window.update_progress(Progress("new", "send", 50, 100, 1, "transferring"))
    assert window.progress.format() == "%p%" and window.progress.value() == 50
    assert not window.archive_button.isEnabled() and window.cancel_button.isEnabled()
    window._archive_transfer()  # An in-progress task cannot be archived or cancelled by this action.
    assert window.active_id == "new" and "new" not in window.archived_transfers
    window.update_progress(Progress("new", "send", 100, 100, 0, "complete"))
    assert window.progress.value() == 100 and window.archive_button.isEnabled()
    window.archive_button.click()
    assert window.progress.isHidden() and len(window.transfers) == 2


@pytest.mark.parametrize("cancelled", [False, True])
async def test_late_network_cleanup_does_not_overwrite_ready_after_archive(
    desktop, qapp, monkeypatch, cancelled
):
    window, worker = desktop
    release = asyncio.Event()
    state = "cancelled" if cancelled else "error: Connection lost"

    async def delayed_failure(identity, trust, peer_id, host, port, paths, progress, token):
        progress(Progress("ended", "send", 32, 100, 0, state))
        await release.wait()  # Models asynchronous TLS cleanup after terminal progress.
        raise TransferCancelled() if cancelled else ProtocolError("Connection lost")

    monkeypatch.setattr("lanbridge.ui.worker.send_files", delayed_failure)
    monkeypatch.setattr(worker, "submit", asyncio.create_task)
    task = worker.send(Peer("a" * 64, "Receiver", "Desktop", "127.0.0.1", 1234), [])
    await asyncio.sleep(0)
    assert window.progress.format() == ("Cancelled" if cancelled else "Failed")
    window.archive_button.click()
    release.set()
    await task
    qapp.processEvents()
    assert window.status.text().startswith("Ready to receive")
    assert window.progress.isHidden() and "ended" in window.archived_transfers
