"""Public-certificate bootstrap authenticated by explicit comparison on both devices.

The bootstrap carries no file bytes or secrets. Every approval is signed over
the session transcript. Transfer is only available on the separate mutual-TLS port.
"""

from __future__ import annotations

import asyncio
import contextlib
import hashlib
import json
import re
import secrets
import time
from collections.abc import Awaitable, Callable

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from lanbridge.core.config import clean_device_name
from lanbridge.core.identity import Identity, TrustStore, fingerprint, parse_certificate
from lanbridge.core.protocol import ProtocolError, receive, send
from lanbridge.network.discovery import Peer

PAIR_TIMEOUT = 120
Approval = Callable[[Peer, str, str], Awaitable[bool]]


def hello(identity: Identity, name: str, port: int) -> dict:
    return {"certificate": identity.pem, "nonce": secrets.token_hex(32), "name": name, "port": port}


def validate_hello(message: dict) -> dict:
    pem = message.get("certificate")
    fingerprint(pem)
    nonce, port = message.get("nonce"), message.get("port")
    if not isinstance(nonce, str) or not re.fullmatch(r"[0-9a-f]{64}", nonce):
        raise ProtocolError("Invalid pairing nonce")
    if type(port) is not int or not 1 <= port <= 65535:
        raise ProtocolError("Invalid transfer port")
    return {
        "certificate": pem,
        "nonce": nonce,
        "name": clean_device_name(message.get("name", "")),
        "port": port,
    }


def transcript(initiator: dict, responder: dict) -> bytes:
    return json.dumps(
        {"purpose": "LanBridge pairing", "v": 1, "initiator": initiator, "responder": responder},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def verification_code(data: bytes) -> str:
    # 96 bits keeps adaptive/birthday searches impractical; compare ALL 6 groups.
    value = hashlib.sha256(b"LanBridge pairing v1\0" + data).hexdigest()[:24].upper()
    return " ".join(value[i : i + 4] for i in range(0, 24, 4))


def verify(pem: str, signature: str, data: bytes):
    try:
        if not isinstance(signature, str) or len(signature) > 256:
            raise ValueError("Invalid signature size")
        parse_certificate(pem).public_key().verify(bytes.fromhex(signature), data, ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise ProtocolError("Pairing signature verification failed") from exc


async def exchange_decisions(
    reader, writer, identity: Identity, remote_pem: str, data: bytes, approved: bool, role: str
):
    def decision_bytes(decision: bool, signer: str):
        return data + b"\0decision\0" + signer.encode("ascii") + (b"\x01" if decision else b"\x00")

    await send(
        writer, "pair_decision", approved=approved, signature=identity.sign(decision_bytes(approved, role))
    )
    reply = await receive(reader, PAIR_TIMEOUT)
    if reply.get("type") != "pair_decision" or type(reply.get("approved")) is not bool:
        raise ProtocolError("Invalid pairing decision")
    verify(
        remote_pem,
        reply.get("signature"),
        decision_bytes(reply["approved"], "responder" if role == "initiator" else "initiator"),
    )
    if not approved or not reply["approved"]:
        raise ProtocolError("Pairing declined; neither side should trust a different code")


class PairingServer:
    def __init__(
        self,
        identity: Identity,
        trust: TrustStore,
        name: str,
        transfer_port: int,
        approval: Approval,
        paired: Callable[[Peer], None] = lambda _: None,
    ):
        self.identity, self.trust, self.name, self.transfer_port = identity, trust, name, transfer_port
        self.approval, self.paired = approval, paired
        self.server = None
        self.allowed_until = 0.0
        self.tasks: set[asyncio.Task] = set()
        self.attempts: dict[str, list[float]] = {}

    def allow(self, seconds=120):
        self.allowed_until = time.monotonic() + seconds

    async def start(self, host="127.0.0.1", port=0) -> int:
        self.server = await asyncio.start_server(self._handle, host, port)
        return self.server.sockets[0].getsockname()[1]

    async def _handle(self, reader, writer):
        task = asyncio.current_task()
        self.tasks.add(task)
        try:
            host = writer.get_extra_info("peername")[0]
            now = time.monotonic()
            self.attempts = {
                key: [t for t in values if t > now - 60]
                for key, values in self.attempts.items()
                if values and values[-1] > now - 60
            }
            attempts = self.attempts.setdefault(host, [])
            if now > self.allowed_until:
                raise ProtocolError("Open LanBridge on the receiver and click Allow pairing first")
            if len(self.tasks) > 2 or len(attempts) >= 5 or len(self.attempts) > 1000:
                raise ProtocolError("Pairing is busy; try again later")
            attempts.append(now)
            async with asyncio.timeout(PAIR_TIMEOUT + 15):
                request = await receive(reader, 10)
                if request.get("type") != "pair_hello":
                    raise ProtocolError("Expected pairing hello")
                remote = validate_hello(request)
                peer_id = fingerprint(remote["certificate"])
                if peer_id == self.identity.id:
                    raise ProtocolError("Cannot pair a device with itself")
                local = hello(self.identity, self.name, self.transfer_port)
                data = transcript(remote, local)
                await send(writer, "pair_challenge", **local, signature=self.identity.sign(data))
                proof = await receive(reader, 10)
                if proof.get("type") != "pair_proof":
                    raise ProtocolError("Missing pairing proof")
                verify(remote["certificate"], proof.get("signature"), data)
                peer = Peer(peer_id, remote["name"], "Desktop", host, remote["port"])
                approved = await asyncio.wait_for(
                    self.approval(peer, verification_code(data), peer_id), PAIR_TIMEOUT
                )
                await exchange_decisions(
                    reader, writer, self.identity, remote["certificate"], data, approved, "responder"
                )
                await send(writer, "pair_ready", signature=self.identity.sign(data + b"\0ready"))
                commit = await receive(reader, 10)
                if commit.get("type") != "pair_commit":
                    raise ProtocolError("Missing pairing commit")
                verify(remote["certificate"], commit.get("signature"), data + b"\0commit")
                self.trust.add(remote["certificate"], remote["name"])
                self.paired(peer)
                await send(writer, "pair_complete", signature=self.identity.sign(data + b"\0complete"))
        except (OSError, ValueError, ProtocolError, TimeoutError, asyncio.IncompleteReadError) as exc:
            with contextlib.suppress(OSError, TimeoutError, ProtocolError):
                await send(writer, "error", message=str(exc)[:300])
        finally:
            self.tasks.discard(task)
            writer.close()
            with contextlib.suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), 2)

    async def close(self):
        if self.server:
            self.server.close()
        tasks = list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if self.server:
            await self.server.wait_closed()


async def pair(
    identity: Identity,
    trust: TrustStore,
    name: str,
    transfer_port: int,
    host: str,
    pair_port: int,
    approval: Approval,
    expected_id: str | None = None,
) -> Peer:
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, pair_port), 10)
    try:
        async with asyncio.timeout(PAIR_TIMEOUT + 15):
            local = hello(identity, name, transfer_port)
            await send(writer, "pair_hello", **local)
            challenge = await receive(reader, 10)
            if challenge.get("type") != "pair_challenge":
                raise ProtocolError(challenge.get("message", "Pairing not available"))
            remote = validate_hello(challenge)
            peer_id = fingerprint(remote["certificate"])
            if peer_id == identity.id or (expected_id is not None and expected_id != peer_id):
                raise ProtocolError("Discovered identity changed; pairing aborted")
            data = transcript(local, remote)
            verify(remote["certificate"], challenge.get("signature"), data)
            await send(writer, "pair_proof", signature=identity.sign(data))
            peer = Peer(peer_id, remote["name"], "Desktop", host, remote["port"], pair_port)
            approved = await asyncio.wait_for(approval(peer, verification_code(data), peer_id), PAIR_TIMEOUT)
            await exchange_decisions(
                reader, writer, identity, remote["certificate"], data, approved, "initiator"
            )
            ready = await receive(reader, 10)
            if ready.get("type") != "pair_ready":
                raise ProtocolError("Pairing was not confirmed")
            verify(remote["certificate"], ready.get("signature"), data + b"\0ready")
            # A disconnect during commit may leave asymmetric trust. Re-pairing
            # with a newly compared code safely repairs it; never auto-approve.
            trust.add(remote["certificate"], remote["name"])
            await send(writer, "pair_commit", signature=identity.sign(data + b"\0commit"))
            complete = await receive(reader, 10)
            if complete.get("type") != "pair_complete":
                raise ProtocolError("Pairing completion not received; pair again")
            verify(remote["certificate"], complete.get("signature"), data + b"\0complete")
            return peer
    finally:
        writer.close()
        with contextlib.suppress(OSError, TimeoutError):
            await asyncio.wait_for(writer.wait_closed(), 2)
