from __future__ import annotations

import asyncio
import ipaddress
import logging
import platform
import re
import socket
from collections.abc import Callable
from dataclasses import dataclass

import ifaddr
from zeroconf import IPVersion, ServiceInfo, ServiceStateChange
from zeroconf.asyncio import AsyncServiceBrowser, AsyncServiceInfo, AsyncZeroconf

from lanbridge.core.config import clean_device_name

SERVICE = "_lanbridge._tcp.local."
log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Peer:
    id: str
    name: str
    os: str
    host: str
    port: int
    pair_port: int = 0


def parse_peer(info: ServiceInfo) -> Peer:
    props = {
        key.decode("ascii"): value.decode("utf-8")
        for key, value in info.properties.items()
        if value is not None
    }
    if props.get("v") != "1" or not re.fullmatch(r"[0-9a-f]{64}", props.get("id", "")):
        raise ValueError("Unsupported discovery record")
    addresses = info.parsed_addresses(IPVersion.V4Only)
    if not addresses or not 1 <= info.port <= 65535:
        raise ValueError("Missing peer endpoint")
    pair_port = int(props.get("pair_port", "0"))
    if not 0 <= pair_port <= 65535:
        raise ValueError("Invalid pairing port")
    # Windows often advertises APIPA addresses for disconnected/virtual adapters
    # before its usable LAN address. DNS record ordering is not a route preference.
    candidates = [ipaddress.IPv4Address(address) for address in addresses]
    usable = [address for address in candidates if not (address.is_unspecified or address.is_multicast)]
    if not usable:
        raise ValueError("Missing usable peer address")
    host = str(min(usable, key=lambda address: (address.is_link_local, int(address))))
    return Peer(
        props["id"],
        clean_device_name(props["name"]),
        clean_device_name(props.get("os", "Desktop")),
        host,
        info.port,
        pair_port,
    )


def local_addresses() -> list[str]:
    addresses = {
        ip.ip
        for adapter in ifaddr.get_adapters()
        for ip in adapter.ips
        if isinstance(ip.ip, str) and not ipaddress.ip_address(ip.ip).is_loopback
    }
    return sorted(addresses) or ["127.0.0.1"]


class Discovery:
    def __init__(
        self,
        device_id: str,
        name: str,
        port: int,
        pair_port: int,
        changed: Callable[[list[Peer]], None],
        *,
        addresses: list[str] | None = None,
    ):
        self.id, self.name, self.changed = device_id, name, changed
        self.addresses = addresses or local_addresses()
        self.info = ServiceInfo(
            SERVICE,
            f"{device_id[:32]}.{SERVICE}",
            addresses=[socket.inet_aton(a) for a in self.addresses],
            port=port,
            properties={
                "v": "1",
                "id": device_id,
                "name": name,
                "os": platform.system(),
                "pair_port": str(pair_port),
            },
            server=f"lanbridge-{device_id[:16]}.local.",
        )
        self.peers: dict[str, Peer] = {}
        self.services: dict[str, str] = {}
        self.tasks: set[asyncio.Task] = set()
        self.zc = None
        self.browser = None

    async def start(self):
        self.zc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        try:
            await self.zc.async_register_service(self.info)
            self.browser = AsyncServiceBrowser(self.zc.zeroconf, SERVICE, handlers=[self._event])
        except BaseException:
            await self.zc.async_close()
            self.zc = None
            raise

    def _event(self, zeroconf, service_type, name, state_change):
        if state_change == ServiceStateChange.Removed:
            peer_id = self.services.pop(name, None)
            if peer_id and peer_id not in self.services.values():
                self.peers.pop(peer_id, None)
                self.changed(list(self.peers.values()))
            return
        task = asyncio.create_task(self._resolve(service_type, name))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)

    async def _resolve(self, service_type: str, name: str):
        info = AsyncServiceInfo(service_type, name)
        try:
            if await info.async_request(self.zc.zeroconf, 2000):
                peer = parse_peer(info)
                if peer.id != self.id:
                    self.services[name] = peer.id
                    self.peers[peer.id] = peer
                    self.changed(list(self.peers.values()))
        except (ValueError, UnicodeError, KeyError) as exc:
            log.debug("Ignored invalid discovery record: %s", exc)

    async def close(self):
        if self.browser:
            await self.browser.async_cancel()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)
        if self.zc:
            await self.zc.async_unregister_service(self.info)
            await self.zc.async_close()
