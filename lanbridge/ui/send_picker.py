"""One-click recipient selection for an explicit file-manager send request."""

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from lanbridge.network.discovery import Peer


class SendPicker(QDialog):
    def __init__(self, paths: list[Path], choose: Callable[[Peer], bool], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Send with LanBridge")
        self.setMinimumSize(440, 280)
        self.peers: dict[str, Peer] = {}
        self.choose = choose
        self.decided = False
        layout = QVBoxLayout(self)
        summary = QLabel(f"Send {len(paths)} file(s)\n" + "\n".join(path.name for path in paths[:5]))
        summary.setTextFormat(Qt.TextFormat.PlainText)
        summary.setWordWrap(True)
        layout.addWidget(summary)
        layout.addWidget(QLabel("Click a paired computer to send now. The receiver must Accept."))
        self.devices = QListWidget()
        self.devices.itemClicked.connect(self._choose)
        self.devices.itemActivated.connect(self._choose)
        layout.addWidget(self.devices)
        self.empty = QLabel(
            "No paired devices online. Open the other computer's app, or cancel and pair it first."
        )
        self.empty.setWordWrap(True)
        layout.addWidget(self.empty)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def set_peers(self, peers: list[Peer]):
        self.peers = {peer.id: peer for peer in peers}
        self.devices.clear()
        for peer in sorted(peers, key=lambda value: value.name.casefold()):
            item = QListWidgetItem(f"{peer.name} · {peer.os}")
            item.setData(Qt.ItemDataRole.UserRole, peer.id)
            self.devices.addItem(item)
        self.empty.setVisible(not peers)

    def _choose(self, item):
        peer = self.peers.get(item.data(Qt.ItemDataRole.UserRole))
        if not self.decided and peer and self.choose(peer):
            self.decided = True
            self.accept()
