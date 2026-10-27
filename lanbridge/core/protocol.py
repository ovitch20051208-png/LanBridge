from __future__ import annotations

import asyncio
import json
import struct
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

VERSION = 1
MAX_FRAME = 65536
CHUNK = 256 * 1024
MAX_FILES = 100
MAX_TOTAL = 1024**4  # 1 TiB per offer; still requires consent and available disk space.
IO_TIMEOUT = 30.0
CONSENT_TIMEOUT = 90.0


class ProtocolError(Exception):
    pass


class TransferCancelled(ProtocolError):
    pass


async def receive(reader: asyncio.StreamReader, timeout: float = IO_TIMEOUT) -> dict:
    async with asyncio.timeout(timeout):
        size = struct.unpack("!I", await reader.readexactly(4))[0]
        if not 0 < size <= MAX_FRAME:
            raise ProtocolError("Control frame exceeds limit")
        try:
            value = json.loads((await reader.readexactly(size)).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ProtocolError("Invalid JSON control frame") from exc
    if not isinstance(value, dict) or type(value.get("v")) is not int or value["v"] != VERSION:
        raise ProtocolError("Unsupported protocol version")
    if not isinstance(value.get("type"), str):
        raise ProtocolError("Missing message type")
    return value


async def send(writer: asyncio.StreamWriter, kind: str, **values) -> None:
    data = json.dumps({"v": VERSION, "type": kind, **values}, ensure_ascii=False, allow_nan=False).encode(
        "utf-8"
    )
    if len(data) > MAX_FRAME:
        raise ProtocolError("Control frame exceeds limit")
    writer.write(struct.pack("!I", len(data)) + data)
    await asyncio.wait_for(writer.drain(), IO_TIMEOUT)


def safe_filename(value: str) -> str:
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 240:
        raise ProtocolError("Invalid filename length")
    if value in {".", ".."} or value[-1] in " ." or any(c in value for c in '/\\:<>"|?*'):
        raise ProtocolError("Unsafe filename")
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ProtocolError("Control characters in filename")
    if value.split(".")[0].upper() in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *[f"COM{i}" for i in range(10)],
        *[f"LPT{i}" for i in range(10)],
    }:
        raise ProtocolError("Reserved filename")
    return value


@dataclass(frozen=True)
class FileSpec:
    name: str
    size: int

    def wire(self) -> dict:
        return {"name": self.name, "size": self.size}


@dataclass(frozen=True)
class Offer:
    id: str
    files: tuple[FileSpec, ...]
    created: int

    @property
    def total(self) -> int:
        return sum(item.size for item in self.files)

    @classmethod
    def parse(cls, message: dict) -> Offer:
        if message.get("type") != "offer":
            raise ProtocolError("Expected transfer offer")
        request_id = message.get("id")
        try:
            if not isinstance(request_id, str) or str(uuid.UUID(request_id)) != request_id:
                raise ValueError()
        except (ValueError, AttributeError) as exc:
            raise ProtocolError("Invalid transfer ID") from exc
        created = message.get("created")
        if type(created) is not int or abs(time.time() - created) > 120:
            raise ProtocolError("Expired transfer request; check device clocks")
        files = message.get("files")
        if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
            raise ProtocolError("Offer must contain 1–100 files")
        result = []
        for item in files:
            if (
                not isinstance(item, dict)
                or type(item.get("size")) is not int
                or not 0 <= item["size"] <= MAX_TOTAL
            ):
                raise ProtocolError("Invalid file size")
            result.append(FileSpec(safe_filename(item.get("name")), item["size"]))
        offer = cls(request_id, tuple(result), created)
        if offer.total > MAX_TOTAL:
            raise ProtocolError("Transfer exceeds size limit")
        return offer

    @classmethod
    def from_paths(cls, paths: list[Path]) -> Offer:
        if not paths or not all(p.is_file() for p in paths):
            raise ProtocolError("Select regular files; folders are not supported in V1")
        return cls.parse(
            {
                "type": "offer",
                "id": str(uuid.uuid4()),
                "created": int(time.time()),
                "files": [FileSpec(safe_filename(p.name), p.stat().st_size).wire() for p in paths],
            }
        )
