from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QColor, QDesktopServices, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from lanbridge import __version__
from lanbridge.core.config import Settings, clean_device_name
from lanbridge.core.protocol import CONSENT_TIMEOUT
from lanbridge.network.discovery import Peer
from lanbridge.ui.worker import Events, NetworkWorker


def human_size(value: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if value < 1024 or unit == "TiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return ""


def app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#3874f2"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(2, 2, 60, 60, 16, 16)
    painter.setPen(QColor("white"))
    font = painter.font()
    font.setPixelSize(31)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "LB")
    painter.end()
    return QIcon(pixmap)


class DecisionDialog(QDialog):
    def __init__(
        self,
        title: str,
        text: str,
        future: concurrent.futures.Future,
        *,
        parent=None,
        accept_label="Accept",
        timeout=CONSENT_TIMEOUT,
    ):
        super().__init__(parent)
        self.future = future
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setMinimumWidth(430)
        layout = QVBoxLayout(self)
        self.text = QLabel(text)
        self.text.setTextFormat(Qt.TextFormat.PlainText)
        self.text.setWordWrap(True)
        layout.addWidget(self.text)
        buttons = QDialogButtonBox()
        self.accept_button = buttons.addButton(accept_label, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Decline", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.deadline = time.monotonic() + timeout
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._check)
        self.timer.start()
        self.finished.connect(self._resolve)

    def _resolve(self, result):
        self.timer.stop()
        if not self.future.done():
            self.future.set_result(result == QDialog.DialogCode.Accepted)

    def _check(self):
        if self.future.done() or time.monotonic() >= self.deadline:
            self.reject()


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings, worker: NetworkWorker, events: Events):
        super().__init__()
        self.settings, self.worker, self.events = settings, worker, events
        self.paths: list[Path] = []
        self.peers: dict[str, Peer] = {}
        self.dialogs: list[QDialog] = []
        self.active_id = None
        self.setWindowTitle("LanBridge")
        self.setWindowIcon(app_icon())
        self.resize(720, 650)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        title = QLabel("LanBridge")
        title.setStyleSheet("font-size: 30px; font-weight: 600")
        layout.addWidget(title)
        self.subtitle = QLabel(f"{settings.name} · private transfers on your local network")
        self.subtitle.setWordWrap(True)
        layout.addWidget(self.subtitle)
        layout.addWidget(QLabel("NEARBY DEVICES"))
        self.device_list = QListWidget()
        self.device_list.setMinimumHeight(160)
        self.device_list.currentItemChanged.connect(self._selection)
        layout.addWidget(self.device_list)
        self.empty = QLabel("Looking for nearby computers… Both devices need LanBridge running.")
        self.empty.setWordWrap(True)
        layout.addWidget(self.empty)
        row = QHBoxLayout()
        self.pair_button = QPushButton("Pair device")
        self.pair_button.clicked.connect(self._pair)
        self.pair_button.setEnabled(False)
        manual = QPushButton("Connect manually…")
        manual.clicked.connect(self._manual)
        row.addWidget(self.pair_button)
        row.addWidget(manual)
        row.addStretch()
        layout.addLayout(row)
        self.files_label = QLabel("Choose files or use Send with LanBridge in your file manager.")
        self.files_label.setWordWrap(True)
        self.files_label.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.files_label)
        row = QHBoxLayout()
        choose = QPushButton("Choose files…")
        choose.clicked.connect(self._choose)
        self.send_button = QPushButton("Send files")
        self.send_button.setObjectName("primary")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._send)
        row.addWidget(choose)
        row.addStretch()
        row.addWidget(self.send_button)
        layout.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status = QLabel("Starting receiver…")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel transfer")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(lambda: self.worker.cancel(self.active_id))
        row.addWidget(self.cancel_button)
        row.addStretch()
        settings_button = QPushButton("Settings…")
        settings_button.clicked.connect(self.show_settings)
        row.addWidget(settings_button)
        layout.addLayout(row)
        self.setStyleSheet(
            "QPushButton { padding: 8px 14px; border-radius: 7px; } QPushButton#primary { background: #3874f2; color: white; } QListWidget { border-radius: 9px; padding: 6px; } QProgressBar { min-height: 14px; border-radius: 6px; }"
        )
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("LanBridge")
        self.tray_menu = QMenu(self)
        for label, action in (
            ("Open LanBridge", self.reveal),
            ("Nearby Devices", self.reveal),
            ("Received Files", self.open_downloads),
            ("Settings", self.show_settings),
            ("Quit", QApplication.instance().quit),
        ):
            entry = QAction(label, self)
            entry.triggered.connect(action)
            self.tray_menu.addAction(entry)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(
            lambda reason: self.reveal() if reason == QSystemTrayIcon.ActivationReason.Trigger else None
        )
        self.tray.show()
        events.peers.connect(self.set_peers)
        events.consent.connect(self.incoming)
        events.progress.connect(self.update_progress)
        events.error.connect(self.show_error)
        events.info.connect(self.status.setText)
        events.received.connect(self.received)
        events.ready.connect(lambda port: self.status.setText(f"Ready to receive · port {port}"))
        events.forwarded.connect(self.set_files)

    def selected_peer(self) -> Peer | None:
        item = self.device_list.currentItem()
        return self.peers.get(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def set_peers(self, peers: list[Peer]):
        selected = self.selected_peer()
        self.peers = {peer.id: peer for peer in peers}
        self.device_list.clear()
        for peer in sorted(self.peers.values(), key=lambda p: p.name.casefold()):
            trusted = peer.id in self.worker.trust.peers
            item = QListWidgetItem(
                f"{peer.name}   ·   {peer.os}\nOnline · {'Paired' if trusted else 'Pairing required'}"
            )
            item.setData(Qt.ItemDataRole.UserRole, peer.id)
            self.device_list.addItem(item)
            if selected and selected.id == peer.id:
                self.device_list.setCurrentItem(item)
        self.empty.setVisible(not peers)
        self._selection()

    def _selection(self, *_):
        peer = self.selected_peer()
        trusted = peer is not None and peer.id in self.worker.trust.peers
        self.send_button.setEnabled(bool(trusted and self.paths))
        self.pair_button.setEnabled(peer is not None and not trusted)

    def _choose(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose files to send")
        if paths:
            self.set_files([Path(p) for p in paths])

    def set_files(self, paths):
        self.paths = [Path(p).absolute() for p in paths]
        if self.paths:
            self.files_label.setText(
                "\n".join(p.name for p in self.paths[:8])
                + (f"\n… {len(self.paths)} files" if len(self.paths) > 8 else "")
            )
        self._selection()
        self.reveal()

    def _send(self):
        if peer := self.selected_peer():
            self.worker.send(peer, list(self.paths))

    def _pair(self):
        if peer := self.selected_peer():
            self.worker.pair(peer)

    def _manual(self):
        text, ok = QInputDialog.getText(
            self,
            "Manual connection",
            "Recipient IPv4 address and transfer port (for example 192.168.1.20:47384):",
        )
        if not ok:
            return
        import ipaddress

        try:
            host, port = text.strip().rsplit(":", 1)
            host = str(ipaddress.IPv4Address(host))
            port = int(port)
            if not 1 <= port <= 65535:
                raise ValueError()
            peer_id, ok = QInputDialog.getText(
                self, "Paired identity", "Full device fingerprint from the other computer's Settings:"
            )
            if not ok:
                return
            if peer_id not in self.worker.trust.peers:
                raise ValueError("Pair the device before a manual transfer")
            record = self.worker.trust.peers[peer_id]
            peer = Peer(peer_id, record["name"], "Desktop", host, port)
            self.set_peers([*self.peers.values(), peer])
        except ValueError as exc:
            self.show_error(str(exc) or "Invalid address or port")

    def _open_dialog(self, dialog: QDialog):
        self.dialogs.append(dialog)
        dialog.finished.connect(lambda _: self.dialogs.remove(dialog) if dialog in self.dialogs else None)
        dialog.open()
        dialog.raise_()
        dialog.activateWindow()

    def incoming(self, payload):
        peer_id, offer, future = payload
        name = self.worker.trust.peers.get(peer_id, {}).get("name", peer_id[:16])
        listing = "\n".join(f"• {item.name} ({human_size(item.size)})" for item in offer.files[:12])
        if len(offer.files) > 12:
            listing += f"\n… and {len(offer.files) - 12} more files"
        self._open_dialog(
            DecisionDialog(
                "Incoming files",
                f"{name} wants to send {len(offer.files)} file(s)\n\n{listing}\n\nTotal: {human_size(offer.total)}\nSave to: {self.settings.downloads}",
                future,
                parent=self,
            )
        )

    def update_progress(self, value):
        self.active_id = value.id
        terminal = value.state in {"complete", "declined", "cancelled"} or value.state.startswith("error:")
        self.cancel_button.setEnabled(not terminal)
        percent = (
            int(value.done * 100 / value.total) if value.total else (100 if value.state == "complete" else 0)
        )
        self.progress.setValue(percent)
        self.status.setText(
            f"{value.direction.capitalize()} · {value.state}\n{human_size(value.done)} / {human_size(value.total)} · {human_size(value.speed)}/s · {human_size(max(0, value.total - value.done))} remaining"
        )

    def received(self, payload):
        _, paths = payload
        self.tray.showMessage("LanBridge", f"Received {len(paths)} file(s) in {self.settings.downloads}")

    def show_error(self, message):
        self.status.setText(message)
        self.tray.showMessage("LanBridge", message, QSystemTrayIcon.MessageIcon.Warning)

    def reveal(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def open_downloads(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.settings.downloads)))

    def show_settings(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("LanBridge settings")
        dialog.setMinimumWidth(540)
        layout = QFormLayout(dialog)
        name = QLineEdit(self.settings.name)
        downloads = QLineEdit(str(self.settings.downloads))
        layout.addRow("Device name", name)
        directory_row = QHBoxLayout()
        directory_row.addWidget(downloads)
        browse = QPushButton("Browse…")
        browse.clicked.connect(
            lambda: downloads.setText(
                QFileDialog.getExistingDirectory(dialog, "Download directory", downloads.text())
                or downloads.text()
            )
        )
        directory_row.addWidget(browse)
        layout.addRow("Save received files to", directory_row)
        identity = QLineEdit(self.worker.identity.id)
        identity.setReadOnly(True)
        layout.addRow("Device fingerprint", identity)
        trusted = QListWidget()
        for peer_id, record in self.worker.trust.peers.items():
            item = QListWidgetItem(f"{record['name']} · {peer_id[:16]}")
            item.setData(Qt.ItemDataRole.UserRole, peer_id)
            trusted.addItem(item)
        layout.addRow("Trusted devices", trusted)
        layout.addRow("Version", QLabel(__version__))
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(buttons)

        def save():
            try:
                self.settings.name = clean_device_name(name.text())
                self.settings.downloads = Path(downloads.text()).expanduser().absolute()
                self.settings.save()
                if self.worker.server:
                    self.worker.server.downloads = self.settings.downloads
                self.subtitle.setText(f"{self.settings.name} · private transfers on your local network")
                self.status.setText("Settings saved. Restart to update the advertised device name.")
                dialog.accept()
            except (OSError, ValueError) as exc:
                QMessageBox.warning(dialog, "Could not save settings", str(exc))

        buttons.accepted.connect(save)
        buttons.rejected.connect(dialog.reject)
        self._open_dialog(dialog)

    def closeEvent(self, event):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.hide()
            event.ignore()
        else:
            # Keep the receiver accessible on desktops lacking a tray.
            event.accept()
            QApplication.instance().quit()
