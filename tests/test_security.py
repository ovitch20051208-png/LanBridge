import asyncio
import contextlib
import struct
import time
import uuid

import pytest

from lanbridge.core.identity import Identity, TrustStore, parse_certificate
from lanbridge.core.protocol import MAX_FRAME, Offer, ProtocolError, TransferCancelled, receive, send
from lanbridge.network.transfer import Cancellation, TransferServer, send_files


async def yes(*_):
    return True


async def connect(peers, port):
    a, at, b, _ = peers
    return await asyncio.open_connection(
        "127.0.0.1", port, ssl=at.context(a, server=False, peer_id=b.id), server_hostname=None
    )


async def disconnect(writer):
    writer.close()
    with contextlib.suppress(OSError):
        await writer.wait_closed()


def offer(name="file.txt", size=4, **changes):
    return {
        "type": "offer",
        "id": str(uuid.uuid4()),
        "created": int(time.time()),
        "files": [{"name": name, "size": size}],
        **changes,
    }


@pytest.mark.parametrize(
    "name",
    ["../evil", "/absolute", "..", "a\\b", "a:b", "CON", "NUL.txt", "bad.", "bad ", "bad\x00.txt", "x" * 241],
)
def test_path_traversal_and_reserved_names(name):
    with pytest.raises(ProtocolError):
        Offer.parse(offer(name))


@pytest.mark.parametrize(
    "changes",
    [{"size": -1}, {"size": True}, {"size": 1024**4 + 1}, {"files": []}, {"created": 0}, {"id": "not-an-id"}],
)
def test_malformed_metadata(changes):
    if "size" in changes:
        message = offer(size=changes["size"])
    else:
        message = offer(**changes)
    with pytest.raises(ProtocolError):
        Offer.parse(message)


async def test_unauthorized_certificate_cannot_offer(peers, tmp_path):
    _, _, b, bt = peers
    stranger = Identity(tmp_path / "stranger")
    strangers_trust = TrustStore(stranger.directory / "trust.json")
    strangers_trust.add(b.pem, "Receiver")
    dialogs = []

    async def consent(*args):
        dialogs.append(args)
        return True

    server = TransferServer(b, bt, tmp_path / "received", consent)
    port = await server.start()
    source = tmp_path / "secret.txt"
    source.write_text("unauthorized")
    try:
        with pytest.raises((OSError, asyncio.IncompleteReadError)):
            await send_files(stranger, strangers_trust, b.id, "127.0.0.1", port, [source])
        assert not dialogs and not server.downloads.exists()
    finally:
        await server.close()


@pytest.mark.parametrize("mode", ["metadata", "oversized", "invalid_json"])
async def test_bad_frames_rejected_before_dialog(peers, tmp_path, mode):
    _, _, b, bt = peers
    dialogs = []

    async def consent(*args):
        dialogs.append(args)
        return True

    server = TransferServer(b, bt, tmp_path / "received", consent)
    port = await server.start()
    reader, writer = await connect(peers, port)
    try:
        if mode == "metadata":
            message = offer("../escape.txt")
            message.pop("type")
            await send(writer, "offer", **message)
        elif mode == "oversized":
            writer.write(struct.pack("!I", MAX_FRAME + 1))
            await writer.drain()
        else:
            writer.write(struct.pack("!I", 1) + b"{")
            await writer.drain()
        assert (await receive(reader))["type"] == "error"
        assert not dialogs and not server.downloads.exists()
    finally:
        await disconnect(writer)
        await server.close()


@pytest.mark.parametrize("failure", ["checksum", "disconnect", "receiver_cancel"])
async def test_failed_stream_removes_staging(peers, tmp_path, failure):
    _, _, b, bt = peers
    downloads = tmp_path / "received"
    server = TransferServer(b, bt, downloads, yes)
    port = await server.start()
    reader, writer = await connect(peers, port)
    message = offer(size=4 if failure == "checksum" else 1024**2)
    try:
        await send(writer, "offer", **{k: v for k, v in message.items() if k != "type"})
        assert (await receive(reader))["type"] == "accepted"
        writer.write(b"bad!")
        await writer.drain()
        if failure == "checksum":
            await send(writer, "file_end", index=0, sha256="0" * 64)
            assert "integrity" in (await receive(reader))["message"]
        elif failure == "receiver_cancel":
            server.cancel(message["id"])
            assert await asyncio.wait_for(reader.read(1), 2) == b""
        else:
            await disconnect(writer)
        for _ in range(100):
            if not list(downloads.iterdir()):
                break
            await asyncio.sleep(0.01)
        assert list(downloads.iterdir()) == []
    finally:
        await disconnect(writer)
        await server.close()


async def test_payload_timeout_reports_reason_and_received_bytes_and_cleans_staging(
    peers, tmp_path, monkeypatch
):
    monkeypatch.setattr("lanbridge.network.transfer.IO_TIMEOUT", 0.5)
    _, _, b, bt = peers
    progress = []
    server = TransferServer(b, bt, tmp_path / "received", yes, progress.append)
    port = await server.start()
    reader, writer = await connect(peers, port)
    payload = b"partial data" * 512
    try:
        message = offer(size=1024**2)
        await send(writer, "offer", **{k: v for k, v in message.items() if k != "type"})
        assert (await receive(reader))["type"] == "accepted"
        writer.write(payload)
        await writer.drain()
        reply = await receive(reader, timeout=3)
        assert reply["type"] == "error" and "Connection timed out" in reply["message"]
        assert progress[-1].done == len(payload)
        assert progress[-1].state == "error: " + reply["message"]
        assert not any(item.state == "complete" for item in progress)
        await disconnect(writer)
        await server.close()
        assert not list(server.downloads.iterdir())
    finally:
        await disconnect(writer)
        await server.close()


async def test_sender_timeout_also_provides_a_nonempty_actionable_error(peers, tmp_path, monkeypatch):
    from lanbridge.network import transfer

    a, at, b, bt = peers
    server = TransferServer(b, bt, tmp_path / "received", yes)
    port = await server.start()
    source = tmp_path / "file.txt"
    source.write_text("test")
    progress = []
    sender_task = asyncio.current_task()
    original_receive = transfer.receive

    async def timed_out(*args, **kwargs):
        if asyncio.current_task() is sender_task:
            raise TimeoutError()
        return await original_receive(*args, **kwargs)

    monkeypatch.setattr(transfer, "receive", timed_out)
    try:
        with pytest.raises(ProtocolError, match="Connection timed out"):
            await send_files(a, at, b.id, "127.0.0.1", port, [source], progress.append)
        assert "Connection timed out" in progress[-1].state
        assert not any(item.state == "complete" for item in progress)
    finally:
        await server.close()


@pytest.mark.parametrize("during", ["consent", "stream"])
async def test_sender_cancellation(peers, tmp_path, during):
    a, at, b, bt = peers
    entered = asyncio.Event()
    token = Cancellation()

    async def consent(*_):
        entered.set()
        if during == "consent":
            await asyncio.sleep(60)
        return True

    downloads = tmp_path / "received"
    server = TransferServer(b, bt, downloads, consent)
    port = await server.start()
    source = tmp_path / "large.bin"
    with source.open("wb") as stream:
        stream.truncate(32 * 1024**2)
    progress = []

    def update(value):
        progress.append(value)
        if during == "stream" and value.done > 0:
            token.cancel()

    task = asyncio.create_task(send_files(a, at, b.id, "127.0.0.1", port, [source], update, token))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        if during == "consent":
            token.cancel()
        with pytest.raises(TransferCancelled):
            await asyncio.wait_for(task, 2)
        for _ in range(100):
            if not server.active:
                break
            await asyncio.sleep(0.01)
        assert not downloads.exists() or not list(downloads.iterdir())
        assert progress[-1].state == "cancelled"
        assert not any(p.state == "complete" for p in progress)
    finally:
        await server.close()


async def test_request_timeout_and_replay_survives_restart(peers, tmp_path):
    _, _, b, bt = peers

    async def no_answer(*_):
        await asyncio.sleep(60)

    server = TransferServer(b, bt, tmp_path / "received", no_answer, consent_timeout=0.05)
    port = await server.start()
    message = offer()
    for attempt in range(2):
        reader, writer = await connect(peers, port)
        await send(writer, "offer", **{k: v for k, v in message.items() if k != "type"})
        reply = await receive(reader)
        assert reply["type"] == "error"
        assert ("timed out" if attempt == 0 else "Replayed") in reply["message"]
        await disconnect(writer)
        await server.close()
        if attempt == 0:
            server = TransferServer(b, bt, tmp_path / "received", yes)
            port = await server.start()


async def test_restart_cleans_only_own_staging(peers, tmp_path):
    _, _, b, bt = peers
    downloads = tmp_path / "received"
    own = downloads / f".lanbridge-{b.id[:16]}-crashed"
    own.mkdir(parents=True)
    (own / ".owner").write_text(b.id)
    (own / "0").write_bytes(b"partial data")
    unrelated = downloads / f".lanbridge-{b.id[:16]}-unrelated"
    unrelated.mkdir()
    (unrelated / ".owner").write_text("a different identity")
    server = TransferServer(b, bt, downloads, yes)
    await server.start()
    try:
        assert not own.exists()
        assert unrelated.exists()
    finally:
        await server.close()


async def test_unpair_revokes_pending_request(peers, tmp_path):
    a, at, b, bt = peers
    entered, release = asyncio.Event(), asyncio.Event()

    async def consent(*_):
        entered.set()
        await release.wait()
        return True

    server = TransferServer(b, bt, tmp_path / "received", consent)
    port = await server.start()
    source = tmp_path / "file.txt"
    source.write_text("must not arrive")
    task = asyncio.create_task(send_files(a, at, b.id, "127.0.0.1", port, [source]))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        bt.remove(a.id)
        release.set()
        with pytest.raises(ProtocolError, match="trusted identity"):
            await task
        assert not server.downloads.exists()
    finally:
        await server.close()


def test_certificate_bundle_injection_rejected(peers):
    a, _, b, _ = peers
    with pytest.raises(ValueError, match="exactly one"):
        parse_certificate(a.pem + b.pem)


async def test_receiver_disconnect_never_reports_success(peers, tmp_path):
    a, at, b, bt = peers
    received = asyncio.Event()
    server = TransferServer(
        b, bt, tmp_path / "received", yes, progress=lambda value: received.set() if value.done > 0 else None
    )
    port = await server.start()
    source = tmp_path / "large.bin"
    with source.open("wb") as stream:
        stream.truncate(64 * 1024**2)
    progress = []
    task = asyncio.create_task(send_files(a, at, b.id, "127.0.0.1", port, [source], progress.append))
    try:
        await asyncio.wait_for(received.wait(), 2)
        await server.close()
        with pytest.raises((OSError, ProtocolError, asyncio.IncompleteReadError)):
            await task
        assert not any(p.state == "complete" for p in progress)
        assert not list(server.downloads.iterdir())
    finally:
        await server.close()
