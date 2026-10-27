# Verification record

Development host: Windows x86-64, Python 3.12.10. Physical macOS machine unavailable.
Milestone commits are individually recoverable in Git history.

## M1 — P2P core

Implemented certificate identities and persisted pins, mutual TLS, bounded v1
messages, receiver consent, streaming, SHA-256, collision-safe finalization and
disconnect errors. Core files: `core/{storage,identity,protocol}.py`,
`network/transfer.py`, `tests/{conftest,test_core}.py` and project documentation.

Validation: `python -m pytest -q` — **8 passed**. Actual loopback TLS tests with
independent configurations cover accepted/declined/empty/Unicode/multiple files,
16 MiB streaming, collisions, offline recipients and identity persistence.

Limitations at this checkpoint: test-provisioned trust only; no GUI, native
integration or user pairing yet. Next: desktop UI and discovery.

## M2 — Desktop application

Added Qt main window, recipient selection, foreground Accept/Decline dialog,
threaded asyncio receiver, progress/speed, settings and tray/menu actions.
Added stable-ID mDNS advertising and browsing (`ui/*`, `network/discovery.py`,
`core/config.py`, entry point, desktop tests and multicast smoke utility).

Validation: **14 pytest tests passed**, including an actual TLS send into the
background desktop worker with acceptance through its Qt dialog. A separate
`python scripts/smoke_discovery.py` run passed: two live mDNS advertisers
discovered each other on this host. The smoke run found and fixed a DNS label
length issue before this commit.

Limitations: pairing UI/protocol and secure single-instance forwarding are
scheduled for M4/M3. Real two-computer discovery and Mac UI remain unverified.
Next: native integrations and single-instance IPC.
