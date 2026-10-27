# Security design and boundaries

LanBridge 0.1.0 is a development build, not an independently audited product.

## Identity and first pairing

Each installation generates an ECDSA P-256 self-signed certificate. SHA-256 of
the certificate is the stable device ID. The private key stays on its computer.
On POSIX, state directories are 0700 and private files 0600. On Windows, the
identity and state directories disable inherited permissions and grant the
current user's SID full control. Same-user malware and local administrators
are outside this threat boundary; no encrypted keychain integration is claimed.

Pairing is disabled for incoming requests until the receiver explicitly allows
it for two minutes. The public bootstrap exchanges certificates, fresh 256-bit
nonces, display names and transfer ports. ECDSA signatures bind the ordered
transcript. Both screens display the same 96-bit session comparison code (six
groups); users must compare **every group** and choose **Codes match on both**.
Do not approve solely because the displayed computer name looks familiar.
Signed decisions prevent a relay from changing Decline to Approve.

This channel carries only public pairing information. It is not a file-transfer
endpoint. A human comparison authenticates first trust; mDNS alone never does.
Interrupting the final pairing commit can leave one side trusted; repeat pairing
and compare the new code on both devices to repair this safely.

## Transfer authorization and privacy

Transfer requires TLS 1.2+ with certificate verification required at both ends.
Only pinned certificates are loaded as trust anchors; the application also
checks the exact presented certificate fingerprint. Hostname checking is not
used because DHCP addresses change; certificate identity pins replace it.
There is no `CERT_NONE`, no plaintext transfer, and no silent security fallback.

Every request separately asks the receiving user for Accept/Decline. Trust does
not enable auto-accept. Removing a device revokes pending/active transfers;
existing listener CA entries are additionally checked against the current pin
store. UUID request IDs, creation-time bounds and a persisted five-minute replay
cache reject repeated offers, including across a receiver restart.

## Resource and filesystem defenses

Control frames are capped at 64 KiB, offers at 100 files / 1 TiB, and streaming
chunks at 256 KiB. Requests expire after 90 seconds, pairing after 120 seconds,
and idle transfer I/O after 30 seconds. Concurrent requests, pairing attempts
and replay-cache entries are bounded. OS firewalls remain in force.

Traversal, alternate data streams, reserved names and control characters are
rejected before consent. Untrusted file names are plain text in dialogs.
All accepted files stream into private staging in the selected destination.
SHA-256 is checked before collision-safe publication; existing files are never
silently overwritten. Hard-link publication is atomic; Windows can safely use
non-replacing rename on filesystems without hard links. POSIX filesystems that
support neither method fail safely. No received file is executed.

On clean cancel/disconnect, staging is deleted. After a crash, the next start
cleans only matching, identity-marked staging directories in the configured
download location. If that location was changed externally after a crash,
inspect the previous location for `.lanbridge-<device-prefix>-*` staging.
Publishing a multi-file batch is not one filesystem transaction. A process crash
during publication may leave some already-verified, complete files. If the final
receipt is lost, files can exist at the receiver while the sender reports a
failure; retrying creates collision-suffixed files rather than overwriting.

## Local IPC

A per-user OS lock selects one primary process for a configuration. Named pipe /
local socket messages require a fresh 256-bit token in the protected config
directory, are size bounded and accept only absolute path lists. Windows socket
permissions restrict access to the current user. macOS socket permission flags
are not reliable; the protected token remains the authentication boundary.

## Review and reporting

Do not submit private keys, IPC tokens, full local state directories or private
file contents with a bug report. Report security issues privately to the project
owner. Signing/notarization, a security audit and physical cross-platform
acceptance remain release gates; automated tests are evidence of tested cases,
not proof that every possible attack has been excluded.
