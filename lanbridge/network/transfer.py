"""Real TLS transfer with consent, bounded memory and receiver completion receipts."""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import os
import shutil
import tempfile
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path

from lanbridge.core.identity import Identity, TrustStore
from lanbridge.core.protocol import (
    CHUNK,
    CONSENT_TIMEOUT,
    IO_TIMEOUT,
    Offer,
    ProtocolError,
    TransferCancelled,
    receive,
    send,
)

log = logging.getLogger(__name__)
Consent = Callable[[str, Offer], Awaitable[bool]]


@dataclass(frozen=True)
class Progress:
    id: str
    direction: str
    done: int
    total: int
    speed: float
    state: str


class Cancellation:
    def __init__(self):
        self.event = threading.Event()

    def cancel(self):
        self.event.set()

    def check(self):
        if self.event.is_set():
            raise TransferCancelled("Transfer cancelled")


def finalize(staged: Path, directory: Path, name: str) -> Path:
    """An atomic hard-link publish cannot replace a competing existing file."""
    stem, suffix = Path(name).stem, Path(name).suffix
    for number in range(10000):
        target = directory / (name if number == 0 else f"{stem} ({number}){suffix}")
        try:
            os.link(staged, target)
            staged.unlink()
            return target
        except FileExistsError:
            continue
        except OSError:
            if os.name == "nt":  # Windows rename fails if target exists, also on volumes without hard links.
                try:
                    os.rename(staged, target)
                    return target
                except FileExistsError:
                    continue
            raise
    raise ProtocolError("Too many filename collisions")


class TransferServer:
    def __init__(
        self,
        identity: Identity,
        trust: TrustStore,
        downloads: Path,
        consent: Consent,
        progress: Callable[[Progress], None] = lambda _: None,
        completed: Callable[[str, list[Path]], None] = lambda *_: None,
        *,
        consent_timeout: float = CONSENT_TIMEOUT,
    ):
        self.identity, self.trust, self.downloads = identity, trust, downloads
        self.consent, self.progress, self.completed = consent, progress, completed
        self.consent_timeout = consent_timeout
        self.server = None
        self.active: dict[str, tuple[asyncio.Task, asyncio.StreamWriter]] = {}
        self.connections: set[asyncio.Task] = set()
        self.seen: dict[str, float] = {}
        self.context = None

    async def start(self, host: str = "127.0.0.1", port: int = 0) -> int:
        self.context = self.trust.context(self.identity, server=True)
        self.server = await asyncio.start_server(
            self._handle, host, port, ssl=self.context, ssl_handshake_timeout=10
        )
        return self.server.sockets[0].getsockname()[1]

    def refresh_trust(self):
        # SSL contexts used by an existing listener share this CA store. Exact pin
        # verification below additionally rejects certificates removed from trust.
        for record in self.trust.peers.values():
            self.context.load_verify_locations(cadata=record["certificate"])

    def cancel(self, request_id: str):
        if request_id in self.active:
            task, writer = self.active[request_id]
            writer.close()
            task.cancel()

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        tasks = list(self.connections)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        task = asyncio.current_task()
        self.connections.add(task)
        offer = None
        stage = None
        published: list[Path] = []
        try:
            if len(self.connections) > 8:
                raise ProtocolError("Receiver is busy")
            peer_id = self.trust.verify_socket(writer)
            offer = Offer.parse(await receive(reader))
            now = time.monotonic()
            self.seen = {key: expiry for key, expiry in self.seen.items() if expiry > now}
            if offer.id in self.seen:
                raise ProtocolError("Replayed transfer request")
            if len(self.seen) >= 10000:
                raise ProtocolError("Request rate limit reached")
            self.seen[offer.id] = now + 300
            self.active[offer.id] = (task, writer)
            accepted = await asyncio.wait_for(self.consent(peer_id, offer), self.consent_timeout)
            if not accepted:
                await send(writer, "declined", id=offer.id)
                self.progress(Progress(offer.id, "receive", 0, offer.total, 0, "declined"))
                return
            # Unpairing while consent is open also revokes this pending offer.
            self.trust.verify_socket(writer, peer_id)
            self.downloads.mkdir(parents=True, exist_ok=True)
            if shutil.disk_usage(self.downloads).free < offer.total + 1024 * 1024:
                raise ProtocolError("Insufficient free space")
            stage = Path(tempfile.mkdtemp(prefix=".lanbridge-", dir=self.downloads))
            if os.name != "nt":
                stage.chmod(0o700)
            await send(writer, "accepted", id=offer.id)
            done, started = 0, time.monotonic()
            for index, spec in enumerate(offer.files):
                digest = hashlib.sha256()
                with (stage / str(index)).open("xb") as output:
                    remaining = spec.size
                    while remaining:
                        data = await asyncio.wait_for(reader.read(min(CHUNK, remaining)), IO_TIMEOUT)
                        if not data:
                            raise ProtocolError("Sender disconnected before completion")
                        output.write(data)
                        digest.update(data)
                        remaining -= len(data)
                        done += len(data)
                        self.progress(
                            Progress(
                                offer.id,
                                "receive",
                                done,
                                offer.total,
                                done / max(time.monotonic() - started, 0.001),
                                "transferring",
                            )
                        )
                    output.flush()
                    os.fsync(output.fileno())
                end = await receive(reader)
                if (
                    end.get("type") != "file_end"
                    or end.get("index") != index
                    or end.get("sha256") != digest.hexdigest()
                ):
                    raise ProtocolError("File integrity verification failed")
            for index, spec in enumerate(offer.files):
                published.append(finalize(stage / str(index), self.downloads, spec.name))
            await send(writer, "complete", id=offer.id, files=[p.name for p in published])
            self.progress(
                Progress(
                    offer.id,
                    "receive",
                    done,
                    offer.total,
                    done / max(time.monotonic() - started, 0.001),
                    "complete",
                )
            )
            self.completed(peer_id, published)
        except asyncio.CancelledError:
            if offer:
                self.progress(Progress(offer.id, "receive", 0, offer.total, 0, "cancelled"))
            raise
        except (OSError, ValueError, ProtocolError, TimeoutError, asyncio.IncompleteReadError) as exc:
            log.info("Incoming transfer failed: %s", exc)
            if offer:
                self.progress(Progress(offer.id, "receive", 0, offer.total, 0, f"error: {exc}"))
            with contextlib.suppress(OSError, TimeoutError, ProtocolError):
                await send(writer, "error", message=str(exc)[:300])
            # If publication failed halfway, remove only files we just created.
            for path in published:
                path.unlink(missing_ok=True)
        finally:
            if stage:
                shutil.rmtree(stage, ignore_errors=True)
            if offer:
                self.active.pop(offer.id, None)
            self.connections.discard(task)
            writer.close()
            with contextlib.suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), 2)


async def send_files(
    identity: Identity,
    trust: TrustStore,
    peer_id: str,
    host: str,
    port: int,
    paths: list[Path],
    progress: Callable[[Progress], None] = lambda _: None,
    cancellation: Cancellation | None = None,
) -> str:
    cancellation = cancellation or Cancellation()
    offer = Offer.from_paths(paths)
    writer = None
    done, started = 0, time.monotonic()
    progress(Progress(offer.id, "send", 0, offer.total, 0, "connecting"))
    try:
        cancellation.check()
        ctx = trust.context(identity, server=False, peer_id=peer_id)
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ctx, server_hostname=None, ssl_handshake_timeout=10), 12
        )
        trust.verify_socket(writer, peer_id)
        await send(
            writer, "offer", id=offer.id, created=offer.created, files=[item.wire() for item in offer.files]
        )
        progress(Progress(offer.id, "send", 0, offer.total, 0, "waiting for acceptance"))
        reply = await receive(reader, CONSENT_TIMEOUT + 5)
        cancellation.check()
        if reply.get("type") == "declined" and reply.get("id") == offer.id:
            progress(Progress(offer.id, "send", 0, offer.total, 0, "declined"))
            return "declined"
        if reply.get("type") != "accepted" or reply.get("id") != offer.id:
            raise ProtocolError(reply.get("message", "Receiver did not accept transfer"))
        started = time.monotonic()
        for index, (path, spec) in enumerate(zip(paths, offer.files, strict=True)):
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                remaining = spec.size
                while remaining:
                    cancellation.check()
                    data = stream.read(min(CHUNK, remaining))
                    if not data:
                        raise ProtocolError("Source file changed during transfer")
                    digest.update(data)
                    writer.write(data)
                    await asyncio.wait_for(writer.drain(), IO_TIMEOUT)
                    remaining -= len(data)
                    done += len(data)
                    progress(
                        Progress(
                            offer.id,
                            "send",
                            done,
                            offer.total,
                            done / max(time.monotonic() - started, 0.001),
                            "transferring",
                        )
                    )
                if stream.read(1):
                    raise ProtocolError("Source file grew during transfer")
            await send(writer, "file_end", index=index, sha256=digest.hexdigest())
        cancellation.check()
        progress(Progress(offer.id, "send", done, offer.total, 0, "verifying"))
        receipt = await receive(reader)
        if receipt.get("type") != "complete" or receipt.get("id") != offer.id:
            raise ProtocolError(receipt.get("message", "Receiver did not confirm completion"))
        progress(
            Progress(
                offer.id, "send", done, offer.total, done / max(time.monotonic() - started, 0.001), "complete"
            )
        )
        return "complete"
    except (OSError, ValueError, ProtocolError, TimeoutError, asyncio.IncompleteReadError) as exc:
        state = "cancelled" if isinstance(exc, TransferCancelled) else f"error: {exc}"
        progress(Progress(offer.id, "send", done, offer.total, 0, state))
        raise
    finally:
        if writer:
            writer.close()
            with contextlib.suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), 2)
