"""Optional real multicast smoke check; requires a multicast-capable LAN."""

import asyncio
import uuid

from lanbridge.network.discovery import Discovery


async def main():
    left_id, right_id = uuid.uuid4().hex * 2, uuid.uuid4().hex * 2
    left, right = [], []
    a = Discovery(left_id, "Smoke A", 47384, 47385, lambda p: left.extend(p))
    b = Discovery(right_id, "Smoke B", 47386, 47387, lambda p: right.extend(p))
    try:
        await a.start()
        await b.start()
        for _ in range(100):
            if any(p.id == right_id for p in left) and any(p.id == left_id for p in right):
                print("PASS: two live mDNS advertisers discovered each other")
                return
            await asyncio.sleep(0.1)
        raise RuntimeError("mDNS discovery not observed; inspect firewall/multicast isolation")
    finally:
        await a.close()
        await b.close()


if __name__ == "__main__":
    asyncio.run(main())
