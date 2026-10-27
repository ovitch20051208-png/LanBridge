import asyncio

import pytest

from lanbridge.core.identity import Identity, TrustStore
from lanbridge.core.protocol import ProtocolError, receive, send
from lanbridge.network.pairing import PairingServer, hello, pair, transcript, verification_code, verify
from lanbridge.network.transfer import TransferServer, send_files


@pytest.fixture
def unpaired(tmp_path):
    a, b = Identity(tmp_path / "alice"), Identity(tmp_path / "bob")
    return a, TrustStore(a.directory / "trust.json"), b, TrustStore(b.directory / "trust.json")


async def yes(*_):
    return True


async def test_pair_then_mutual_tls_transfer(unpaired, tmp_path):
    a, at, b, bt = unpaired
    codes = []

    async def approve(peer, code, fingerprint):
        assert peer.id == fingerprint
        codes.append(code)
        return True

    receiver = TransferServer(b, bt, tmp_path / "received", yes)
    transfer_port = await receiver.start()
    bootstrap = PairingServer(b, bt, "Bob", transfer_port, approve, lambda _: receiver.refresh_trust())
    bootstrap.allow()
    pair_port = await bootstrap.start()
    try:
        remote = await pair(a, at, "Alice", 47384, "127.0.0.1", pair_port, approve, b.id)
        assert remote.id == b.id
        assert len(codes) == 2 and codes[0] == codes[1] and len(codes[0].split()) == 6
        assert b.id in TrustStore(at.path).peers and a.id in TrustStore(bt.path).peers
        source = tmp_path / "paired.txt"
        source.write_text("Paired without pre-provisioned trust")
        assert await send_files(a, at, b.id, remote.host, remote.port, [source]) == "complete"
        assert (tmp_path / "received/paired.txt").read_bytes() == source.read_bytes()
    finally:
        await bootstrap.close()
        await receiver.close()


@pytest.mark.parametrize("declining", ["sender", "receiver"])
async def test_pair_requires_both_approvals(unpaired, declining):
    a, at, b, bt = unpaired

    async def initiator(*_):
        return declining != "sender"

    async def responder(*_):
        return declining != "receiver"

    server = PairingServer(b, bt, "Bob", 47384, responder)
    server.allow()
    port = await server.start()
    try:
        with pytest.raises(ProtocolError, match="declined"):
            await pair(a, at, "Alice", 47384, "127.0.0.1", port, initiator)
        assert not at.peers and not bt.peers
    finally:
        await server.close()


async def test_pairing_closed_by_default(unpaired):
    a, at, b, bt = unpaired
    server = PairingServer(b, bt, "Bob", 47384, yes)
    port = await server.start()
    try:
        with pytest.raises(ProtocolError, match="Allow pairing"):
            await pair(a, at, "Alice", 47384, "127.0.0.1", port, yes)
        assert not at.peers and not bt.peers
    finally:
        await server.close()


async def test_discovery_identity_substitution_rejected(unpaired):
    a, at, b, bt = unpaired
    server = PairingServer(b, bt, "Bob", 47384, yes)
    server.allow()
    port = await server.start()
    try:
        with pytest.raises(ProtocolError, match="identity changed"):
            await pair(a, at, "Alice", 47384, "127.0.0.1", port, yes, "f" * 64)
        assert not at.peers and not bt.peers
    finally:
        await server.close()


def test_session_binding_and_signature(unpaired):
    a, _, b, _ = unpaired
    first = transcript(hello(a, "Alice", 47384), hello(b, "Bob", 47384))
    second = transcript(hello(a, "Alice", 47384), hello(b, "Bob", 47384))
    assert verification_code(first) != verification_code(second)
    verify(a.pem, a.sign(first), first)
    with pytest.raises(ProtocolError):
        verify(a.pem, a.sign(first), second)
    with pytest.raises(ProtocolError):
        verify(b.pem, a.sign(first), first)


async def test_network_attacker_cannot_forge_approval(unpaired):
    a, at, b, bt = unpaired

    async def decline(*_):
        return False

    server = PairingServer(b, bt, "Bob", 47384, decline)
    server.allow()
    port = await server.start()
    tasks = set()

    async def relay(reader, writer):
        task = asyncio.current_task()
        tasks.add(task)
        other_reader, other_writer = await asyncio.open_connection("127.0.0.1", port)

        async def pipe(source, destination, tamper=False):
            try:
                while True:
                    frame = await receive(source)
                    if tamper and frame["type"] == "pair_decision":
                        frame["approved"] = True  # Cannot forge the signature.
                    kind = frame.pop("type")
                    frame.pop("v")
                    await send(destination, kind, **frame)
            finally:
                destination.close()

        children = [
            asyncio.create_task(pipe(reader, other_writer)),
            asyncio.create_task(pipe(other_reader, writer, True)),
        ]
        try:
            await asyncio.wait(children, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for child in children:
                child.cancel()
            await asyncio.gather(*children, return_exceptions=True)
            other_writer.close()
            writer.close()
            tasks.discard(task)

    proxy = await asyncio.start_server(relay, "127.0.0.1", 0)
    try:
        with pytest.raises(ProtocolError, match="signature"):
            await pair(a, at, "Alice", 47384, "127.0.0.1", proxy.sockets[0].getsockname()[1], yes)
        assert not at.peers and not bt.peers
    finally:
        proxy.close()
        await proxy.wait_closed()
        for task in list(tasks):
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await server.close()
