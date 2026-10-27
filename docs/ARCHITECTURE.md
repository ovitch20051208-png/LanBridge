# LanBridge architecture

Python 3.12+, PySide6, asyncio networking on a dedicated thread. The Qt thread
owns all widgets; queued signals and futures connect user decisions to network
tasks. Every installation is both a sender and a receiver. No external service
is used at runtime.

* `core`: persistent certificate identity, settings, trust, bounded wire models.
* `network`: TCP/TLS streams, consent, SHA-256, temporary staging, mDNS, pairing.
* `ui`: nearby peers, file selection, incoming consent, progress, tray, settings.
* `ipc`: per-user single-instance locking and authenticated loopback forwarding.
* `platform`: user-level Finder/Send To integration and optional login startup.

## Connections and trust

Each device generates a self-signed certificate and a private key. Its SHA-256
certificate fingerprint is its stable device ID. Discovery is untrusted and
never grants permission to write files. A separate bounded bootstrap protocol
exchanges public certificates and fresh nonces. Users must compare a session
verification code on BOTH computers and explicitly approve. Only public
certificates enter the trust store. File transfer requires mutually verified
TLS (TLS 1.2 minimum), plus exact certificate pin checks; no insecure fallback.
Pairing bootstrap carries no files, private keys or credentials.

## Transfer protocol v1

Control frames: 4-byte unsigned network-order length followed by UTF-8 JSON,
maximum 64 KiB. Every message has protocol version and type. The sender offers
an unpredictable UUID, creation timestamp and bounded file list. The receiver
checks authorization, freshness, replay cache and metadata before asking for
consent. Decline or timeout sends no file bytes. Accept permits exact-length
streaming in 256 KiB chunks; each file is followed by a SHA-256 digest frame.
All files are validated in private staging before collision-safe finalization.
The sender reports success only after a matching receiver completion receipt.

Cancellation closes the connection and removes unfinished staging. Progress
callbacks must be fast; disk/hash operations run off the UI thread. Idle I/O,
consent, pairing and connect operations have deadlines. A transfer can be
restarted after interruption; resume and whole-batch atomicity are not promised.

## Persistence and deployment

Per-user OS config/data directories contain identity, pins, settings and IPC
token. POSIX modes and Windows current-user ACLs protect private files. No
secrets are checked into Git. Executables embed Python with PyInstaller; native
builds run on their target platform. Unsigned development builds are identified
as such; signing/notarization require separately supplied credentials.

## Validation limits

Loopback tests validate actual encrypted sockets, isolated identities and file
content. Qt tests run offscreen. mDNS live tests and native file-manager actions
also require real network/desktop acceptance. Mac-to-Windows behavior must be
verified on both physical systems; a Windows-only development run cannot prove it.
