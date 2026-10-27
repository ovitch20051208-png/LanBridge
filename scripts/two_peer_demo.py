"""Reproducible two-process integration demo with isolated, temporary identities.

Only this test harness makes automatic transfer decisions. The desktop app
always asks the receiving user. Pairing codes are compared by the parent harness.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from lanbridge.core.identity import Identity, TrustStore
from lanbridge.network.pairing import PairingServer, pair
from lanbridge.network.transfer import TransferServer, send_files


def emit(event, **values):
    print(json.dumps({"event": event, **values}), flush=True)


async def child(root: Path, decline: bool):
    identity = Identity(root / "receiver")
    trust = TrustStore(identity.directory / "trust.json")

    async def consent(*_):
        return not decline

    async def approval(peer, code, fingerprint):
        emit("pairing", code=code)
        return (await asyncio.to_thread(sys.stdin.readline)).strip() == "approve"

    receiver = TransferServer(identity, trust, root / "downloads", consent)
    tls_port = await receiver.start()
    bootstrap = PairingServer(
        identity, trust, "Receiver process", tls_port, approval, lambda _: receiver.refresh_trust()
    )
    bootstrap.allow()
    pair_port = await bootstrap.start()
    emit("ready", tls_port=tls_port, pair_port=pair_port)
    try:
        # Avoid racing the approval callback for stdin; wait for committed trust.
        while not trust.peers:
            await asyncio.sleep(0.01)
        await asyncio.to_thread(sys.stdin.readline)
    finally:
        await bootstrap.close()
        await receiver.close()


async def parent(root: Path, decline: bool):
    process = subprocess.Popen(
        [sys.executable, __file__, "--child", "--root", str(root), *(["--decline"] if decline else [])],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    async def read_event():
        line = await asyncio.wait_for(asyncio.to_thread(process.stdout.readline), 10)
        if not line:
            raise RuntimeError("Receiver process exited before reporting readiness")
        return json.loads(line)

    try:
        ready = await read_event()
        assert ready["event"] == "ready"
        identity = Identity(root / "sender")
        trust = TrustStore(identity.directory / "trust.json")

        async def compare_codes(peer, code, fingerprint):
            remote = await read_event()
            matched = remote["event"] == "pairing" and remote["code"] == code
            process.stdin.write("approve\n" if matched else "decline\n")
            process.stdin.flush()
            return matched

        peer = await pair(
            identity, trust, "Sender process", 47384, "127.0.0.1", ready["pair_port"], compare_codes
        )
        source = root / "你好 transfer.bin"
        with source.open("wb") as output:
            for _ in range(48):
                output.write(bytes(range(256)) * 1024)
        empty = root / "empty.txt"
        empty.touch()
        status = await send_files(identity, trust, peer.id, peer.host, peer.port, [source, empty])
        assert status == ("declined" if decline else "complete")
        if decline:
            assert not (root / "downloads").exists()
        else:
            with source.open("rb") as left, (root / "downloads" / source.name).open("rb") as right:
                assert (
                    hashlib.file_digest(left, "sha256").digest()
                    == hashlib.file_digest(right, "sha256").digest()
                )
            assert (root / "downloads/empty.txt").stat().st_size == 0
        emit("passed", status=status, processes=2, paired=True, bytes=source.stat().st_size)
    finally:
        if process.poll() is None:
            process.stdin.write("quit\n")
            process.stdin.flush()
            try:
                await asyncio.wait_for(asyncio.to_thread(process.wait), 5)
            except TimeoutError:
                process.kill()
                process.wait()
        error = process.stderr.read()
        if process.returncode:
            raise RuntimeError(f"Receiver failed: {error}")
        process.stdin.close()
        process.stdout.close()
        process.stderr.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--decline", action="store_true")
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    if args.child:
        asyncio.run(child(args.root, args.decline))
    else:
        with contextlib.ExitStack() as stack:
            root = args.root or Path(
                stack.enter_context(tempfile.TemporaryDirectory(prefix="lanbridge-demo-"))
            )
            asyncio.run(parent(root, args.decline))


if __name__ == "__main__":
    main()
