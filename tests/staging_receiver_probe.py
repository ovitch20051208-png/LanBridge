"""Child of the bounded native ACL test; never use an existing user's state."""

import asyncio
import faulthandler
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from lanbridge.core.identity import Identity, TrustStore
from lanbridge.core.protocol import ProtocolError
from lanbridge.network.transfer import TransferServer, send_files


async def probe(root: Path, sid: str):
    left, right = Identity(root / "left"), Identity(root / "right")
    lt, rt = TrustStore(left.directory / "trust.json"), TrustStore(right.directory / "trust.json")
    # Isolated test provisioning; production still requires both pairing approvals.
    lt.add(right.pem, "Receiver")
    rt.add(left.pem, "Sender")
    downloads = root / "received"
    source = root / "hello.txt"
    source.write_bytes(b"Native NTFS permission regression\n")
    sentinel = downloads / source.name
    original = sentinel.read_bytes()
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    sender, receiver, decisions = [], [], []

    async def consent(_peer, offer):
        decisions.append(offer.id)
        return True

    server = TransferServer(right, rt, downloads, consent, receiver.append)
    port = await server.start()
    elapsed = []
    try:
        assert os.access(downloads, os.W_OK)
        try:
            (downloads / "direct-probe").mkdir()
        except PermissionError as exc:
            assert exc.winerror == 5
        else:
            raise AssertionError("ACL did not deny real mkdir")
        for attempt in range(2):
            started = time.monotonic()
            try:
                await asyncio.wait_for(
                    send_files(left, lt, right.id, "127.0.0.1", port, [source], sender.append), 2
                )
            except ProtocolError as exc:
                assert "[WinError 5]" in str(exc), str(exc)
            else:
                raise AssertionError("Denied transfer must fail")
            elapsed.append(time.monotonic() - started)
            assert sender[-1].state.startswith("error: ") and sender[-1].done == 0
            assert receiver[-1].state.startswith("error: ") and receiver[-1].done == 0
            assert len(decisions) == attempt + 1
            assert not server.active and not server.active_peers
            assert list(downloads.iterdir()) == [sentinel]
            assert sentinel.read_bytes() == original
        subprocess.run(
            ["icacls", str(downloads), "/remove:d", f"*{sid}"], capture_output=True, check=True, timeout=5
        )
        assert (
            await asyncio.wait_for(
                send_files(left, lt, right.id, "127.0.0.1", port, [source], sender.append), 2
            )
            == "complete"
        )
        assert len(decisions) == 3
        assert receiver[-1].state == sender[-1].state == "complete"
        assert sentinel.read_bytes() == original
        received = downloads / "hello (1).txt"
        assert hashlib.sha256(received.read_bytes()).hexdigest() == source_hash
        assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
        assert not list(downloads.glob(".lanbridge-*"))
        print(
            json.dumps(
                {
                    "denied_seconds": elapsed,
                    "consents": len(decisions),
                    "recovery": "complete",
                    "sha256": source_hash,
                }
            )
        )
    finally:
        await server.close()


if __name__ == "__main__":
    faulthandler.dump_traceback_later(4)
    try:
        asyncio.run(probe(Path(sys.argv[1]), sys.argv[2]))
    finally:
        faulthandler.cancel_dump_traceback_later()
