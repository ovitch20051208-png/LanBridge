import asyncio
import hashlib

import pytest

from lanbridge.core.identity import Identity
from lanbridge.core.protocol import Offer, ProtocolError
from lanbridge.network.transfer import TransferServer, send_files


async def yes(*_):
    return True


async def no(*_):
    return False


@pytest.mark.parametrize(
    "content,name", [(b"hello", "hello.txt"), (b"", "empty.bin"), ("跨平台 ✓".encode(), "你好 world.txt")]
)
async def test_real_tls_transfer(peers, tmp_path, content, name):
    a, at, b, bt = peers
    source = tmp_path / name
    source.write_bytes(content)
    downloads = tmp_path / "downloads"
    progress = []
    server = TransferServer(b, bt, downloads, yes)
    port = await server.start()
    try:
        assert await send_files(a, at, b.id, "127.0.0.1", port, [source], progress.append) == "complete"
        assert (downloads / name).read_bytes() == content
        assert progress[-1].state == "complete"
        assert not list(downloads.glob(".lanbridge-*"))
    finally:
        await server.close()


async def test_decline_writes_nothing(peers, tmp_path):
    a, at, b, bt = peers
    source = tmp_path / "secret.txt"
    source.write_text("never sent")
    downloads = tmp_path / "downloads"
    server = TransferServer(b, bt, downloads, no)
    port = await server.start()
    try:
        assert await send_files(a, at, b.id, "127.0.0.1", port, [source]) == "declined"
        assert not downloads.exists()
    finally:
        await server.close()


async def test_multifile_collision_and_streaming(peers, tmp_path):
    a, at, b, bt = peers
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    (downloads / "same.txt").write_text("original")
    left, right = tmp_path / "left", tmp_path / "right"
    left.mkdir()
    right.mkdir()
    p1, p2, large = left / "same.txt", right / "same.txt", left / "large.bin"
    p1.write_text("one")
    p2.write_text("two")
    with large.open("wb") as stream:
        for _ in range(64):
            stream.write(bytes(range(256)) * 1024)
    progress = []
    server = TransferServer(b, bt, downloads, yes)
    port = await server.start()
    try:
        await send_files(a, at, b.id, "127.0.0.1", port, [p1, p2, large], progress.append)
        assert (downloads / "same.txt").read_text() == "original"
        assert (downloads / "same (1).txt").read_text() == "one"
        assert (downloads / "same (2).txt").read_text() == "two"
        assert (
            hashlib.file_digest(large.open("rb"), "sha256").digest()
            == hashlib.file_digest((downloads / large.name).open("rb"), "sha256").digest()
        )
        assert len([p for p in progress if p.state == "transferring"]) >= 64
    finally:
        await server.close()


async def test_offline_recipient(peers, tmp_path):
    a, at, b, _ = peers
    source = tmp_path / "file.txt"
    source.write_text("test")
    probe = await asyncio.start_server(lambda *_: None, "127.0.0.1", 0)
    port = probe.sockets[0].getsockname()[1]
    probe.close()
    await probe.wait_closed()
    with pytest.raises(OSError):
        await send_files(a, at, b.id, "127.0.0.1", port, [source])


def test_identity_persists(tmp_path):
    first = Identity(tmp_path / "identity")
    assert Identity(first.directory).id == first.id


def test_folders_rejected(tmp_path):
    with pytest.raises(ProtocolError):
        Offer.from_paths([tmp_path])
