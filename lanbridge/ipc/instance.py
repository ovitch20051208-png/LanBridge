"""Per-user named-pipe/local-socket IPC, protected by an OS lock and random token."""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
import struct
import time
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from lanbridge.core.protocol import MAX_FILES, MAX_FRAME
from lanbridge.core.storage import read_json, write_json

log = logging.getLogger(__name__)


def validate_request(message: dict, token: str) -> list[Path]:
    if not isinstance(message, dict) or not isinstance(message.get("token"), str):
        raise ValueError("Invalid IPC request")
    if not secrets.compare_digest(message["token"], token) or message.get("v") != 1:
        raise ValueError("IPC authentication failed")
    paths = message.get("files")
    if not isinstance(paths, list) or len(paths) > MAX_FILES:
        raise ValueError("Too many selected files")
    if any(not isinstance(p, str) or "\0" in p or len(p) > 32767 or not Path(p).is_absolute() for p in paths):
        raise ValueError("Invalid selected file path")
    return [Path(p) for p in paths]


class SingleInstance:
    def __init__(self, directory: Path, selected: Callable[[list[Path]], None]):
        self.directory, self.selected = directory, selected
        self.name = (
            "lanbridge-" + hashlib.sha256(str(directory.resolve()).casefold().encode()).hexdigest()[:32]
        )
        self.lock = QLockFile(str(directory / "instance.lock"))
        self.lock.setStaleLockTime(0)
        self.server = QLocalServer()
        self.server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
        self.server.newConnection.connect(self._connections)
        self.token = ""
        self.clients: dict[QLocalSocket, bytearray] = {}
        self.owner = False

    def acquire(self) -> bool:
        if not self.lock.tryLock(0):
            return False
        self.owner = True
        QLocalServer.removeServer(self.name)
        self.token = secrets.token_hex(32)
        if not self.server.listen(self.name):
            self.close()
            raise OSError(f"Could not open local IPC: {self.server.errorString()}")
        write_json(self.directory / "ipc.json", {"v": 1, "token": self.token})
        return True

    def forward(self, paths: list[Path], timeout: float = 6) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                token = read_json(self.directory / "ipc.json", {}).get("token")
                if token:
                    socket = QLocalSocket()
                    socket.connectToServer(self.name)
                    if socket.waitForConnected(150):
                        log.debug("IPC connected")
                        data = json.dumps(
                            {"v": 1, "token": token, "files": [str(p.absolute()) for p in paths]},
                            ensure_ascii=False,
                        ).encode("utf-8")
                        if len(data) > MAX_FRAME:
                            raise ValueError("Selected paths exceed IPC message limit")
                        socket.write(struct.pack("!I", len(data)) + data)
                        socket.waitForBytesWritten(1000)
                        if socket.bytesAvailable() or socket.waitForReadyRead(2000):
                            reply = bytes(socket.readAll())
                            log.debug("IPC reply: %r", reply)
                            accepted = reply == b"OK"
                            socket.disconnectFromServer()
                            return accepted
                        socket.abort()
                        log.debug("IPC read failed: %s", socket.errorString())
            except (OSError, json.JSONDecodeError):
                pass  # The primary may still be initializing its endpoint.
            time.sleep(0.05)
        return False

    def _connections(self):
        log.debug("IPC connection accepted")
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if len(self.clients) >= 16:
                socket.abort()
                socket.deleteLater()
                continue
            self.clients[socket] = bytearray()
            socket.readyRead.connect(lambda sock=socket: self._read(sock))
            socket.disconnected.connect(lambda sock=socket: self._discard(sock))
            from PySide6.QtCore import QTimer

            timer = QTimer(socket)
            timer.setSingleShot(True)
            timer.timeout.connect(socket.abort)
            timer.start(3000)
            self._read(socket)

    def _discard(self, socket):
        self.clients.pop(socket, None)
        socket.deleteLater()

    def _read(self, socket):
        if socket not in self.clients:
            return
        buffer = self.clients[socket]
        buffer.extend(bytes(socket.readAll()))
        log.debug("IPC buffered %d bytes", len(buffer))
        if len(buffer) < 4:
            return
        size = struct.unpack("!I", buffer[:4])[0]
        if not 0 < size <= MAX_FRAME or len(buffer) > MAX_FRAME + 4:
            socket.abort()
            return
        if len(buffer) < size + 4:
            return
        try:
            paths = validate_request(json.loads(buffer[4:].decode("utf-8")), self.token)
            self.selected(paths)
            socket.write(b"OK")
            socket.flush()
            socket.disconnectFromServer()
        except (ValueError, UnicodeError, RecursionError):
            socket.abort()

    def close(self):
        for socket in list(self.clients):
            socket.abort()
        self.server.close()
        if self.owner:
            (self.directory / "ipc.json").unlink(missing_ok=True)
            self.lock.unlock()
            self.owner = False
