from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from lanbridge.core.config import Settings
from lanbridge.core.identity import Identity, TrustStore
from lanbridge.core.protocol import TransferCancelled
from lanbridge.network.discovery import Discovery, Peer
from lanbridge.network.pairing import PairingServer, pair
from lanbridge.network.transfer import Cancellation, TransferServer, send_files

log = logging.getLogger(__name__)


class Events(QObject):
    peers = Signal(object)
    consent = Signal(object)
    pairing = Signal(object)
    progress = Signal(object)
    error = Signal(str)
    info = Signal(str)
    ready = Signal(int)
    received = Signal(object)
    forwarded = Signal(object)
    paired = Signal(object)


class NetworkWorker:
    def __init__(self, settings: Settings, events: Events, *, port: int = 47384, discovery: bool = True):
        self.settings, self.events = settings, events
        self.port, self.enable_discovery = port, discovery
        self.identity = Identity(settings.directory / "identity")
        self.trust = TrustStore(self.identity.directory / "trust.json")
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, name="LanBridge-network", daemon=True)
        self.server = None
        self.discovery = None
        self.pairing = None
        self.pair_port = 0
        self.send_peers: dict[str, str] = {}
        self.sends: dict[str, tuple[asyncio.Task, Cancellation]] = {}
        self.pending: set[concurrent.futures.Future] = set()

    def start(self):
        self.thread.start()

    def _run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._start())
        self.loop.run_forever()
        self.loop.close()

    async def decision(self, signal, payload) -> bool:
        future = concurrent.futures.Future()
        self.pending.add(future)
        signal.emit((*payload, future))
        try:
            return await asyncio.wrap_future(future)
        finally:
            self.pending.discard(future)

    async def _consent(self, peer_id, offer):
        return await self.decision(self.events.consent, (peer_id, offer))

    async def _pair_approval(self, peer, code, fingerprint):
        return await self.decision(self.events.pairing, (peer, code, fingerprint))

    def _paired(self, peer):
        self.server.refresh_trust()
        self.events.paired.emit(peer)
        self.events.info.emit(f"Paired with {peer.name}. File transfers still require Accept.")

    async def _start(self):
        try:
            self.server = TransferServer(
                self.identity,
                self.trust,
                self.settings.downloads,
                self._consent,
                self.events.progress.emit,
                lambda peer_id, paths: self.events.received.emit((peer_id, paths)),
            )
            self.port = await self.server.start("0.0.0.0", self.port)
            self.pairing = PairingServer(
                self.identity, self.trust, self.settings.name, self.port, self._pair_approval, self._paired
            )
            self.pair_port = await self.pairing.start("0.0.0.0")
            if self.enable_discovery:
                self.discovery = Discovery(
                    self.identity.id, self.settings.name, self.port, self.pair_port, self.events.peers.emit
                )
                try:
                    await self.discovery.start()
                except OSError as exc:
                    self.events.error.emit(f"Discovery unavailable: {exc}. You can connect manually.")
            self.events.ready.emit(self.port)
        except Exception as exc:
            log.exception("Receiver startup failed")
            self.events.error.emit(f"Receiver could not start: {exc}")

    def submit(self, coroutine):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop)

    def send(self, peer: Peer, paths: list[Path]):
        async def run():
            task = asyncio.current_task()
            cancel = Cancellation()
            current_id = None

            def progress(value):
                nonlocal current_id
                current_id = value.id
                self.sends[value.id] = (task, cancel)
                self.send_peers[value.id] = peer.id
                self.events.progress.emit(value)

            try:
                await send_files(
                    self.identity, self.trust, peer.id, peer.host, peer.port, paths, progress, cancel
                )
            except (asyncio.CancelledError, TransferCancelled):
                self.events.info.emit("Transfer cancelled")
            except Exception as exc:
                self.events.error.emit(f"Could not send files: {exc}")
            finally:
                if current_id:
                    self.sends.pop(current_id, None)
                    self.send_peers.pop(current_id, None)

        return self.submit(run())

    def pair(self, peer: Peer):
        return self.pair_address(peer.host, peer.pair_port, peer.id)

    def pair_address(self, host: str, port: int, expected_id=None):
        async def run():
            try:
                if not self.pairing or not port:
                    raise ValueError("Wait for the receiver to start and check the pairing port")
                peer = await pair(
                    self.identity,
                    self.trust,
                    self.settings.name,
                    self.port,
                    host,
                    port,
                    self._pair_approval,
                    expected_id,
                )
                self._paired(peer)
            except TimeoutError:
                self.events.error.emit(
                    f"Could not pair: timed out connecting to {host}:{port} or waiting for confirmation. "
                    "Check the other computer's LAN address, firewall and Allow pairing, then try again."
                )
            except Exception as exc:
                self.events.error.emit(f"Could not pair: {exc}")

        return self.submit(run())

    def allow_pairing(self):
        def action():
            if self.pairing:
                self.pairing.allow()
                self.events.info.emit(
                    f"Pairing allowed for 2 minutes · pairing port {self.pair_port}. Compare every code group on both devices."
                )

        self.loop.call_soon_threadsafe(action)

    def unpair(self, peer_id):
        def action():
            self.trust.remove(peer_id)
            self.server.revoke(peer_id)
            for request_id, owner in list(self.send_peers.items()):
                if owner == peer_id:
                    self.cancel(request_id)
            self.events.paired.emit(None)

        self.loop.call_soon_threadsafe(action)

    def cancel(self, request_id: str):
        def action():
            if request_id in self.sends:
                task, cancel = self.sends[request_id]
                cancel.cancel()
                task.cancel()
            if self.server:
                self.server.cancel(request_id)

        self.loop.call_soon_threadsafe(action)

    async def _shutdown(self):
        for future in list(self.pending):
            future.cancel()
        for task, cancel in list(self.sends.values()):
            cancel.cancel()
            task.cancel()
        if self.discovery:
            await self.discovery.close()
        if self.pairing:
            await self.pairing.close()
        if self.server:
            await self.server.close()
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def stop(self):
        if self.thread.is_alive():
            try:
                self.submit(self._shutdown()).result(timeout=8)
            finally:
                self.loop.call_soon_threadsafe(self.loop.stop)
                self.thread.join(timeout=3)
