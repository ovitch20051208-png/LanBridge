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

## M3 — Native integration and single instance

Added current-user IPC lock, random token, bounded local-socket/named-pipe
messages and argument forwarding. Added Windows Send To shortcut, generated
Finder Quick Action, install/removal UI and CLI, and opt-in login startup.
Files: `ipc/instance.py`, `platform/integration.py`, app entry point/settings,
installation guide and native integration tests.

Validation: **18 tests passed**. An independent Python process forwarded paths
with spaces and Chinese characters through the real IPC endpoint, and lock
reacquisition after shutdown passed. Windows COM created a real `.lnk` in a test
directory. Finder workflow plist and shell quoting were validated structurally.

Limitations: Finder execution, login startup and actual Explorer/Finder user
interaction still need manual verification; no claim of Mac execution is made.
Next: session-verified pairing, revocation and adversarial reliability coverage.

## M4 — Security and reliability

Added bounded, signed pairing with a 96-bit session code and approval on both
devices, opt-in pairing window, persisted certificate pins, manual pairing,
revocation, persistent replay cache, cancel/disconnect cleanup and restart cleanup.
The GUI now supports selectable transfer history and notifications. Added
security design, physical acceptance checklist and a two-process demo.

Validation: **60 tests passed** (full suite), with real TLS and process-level
networking. Coverage includes all 15 requested acceptance categories: identity /
discovery, pairing, accept, decline, empty, multiple, Unicode, collisions,
streaming, interruptions, untrusted peers, malformed input, checksum failure,
cancel and receiver restart/disconnect. An active relay changing a signed
Decline to Approve is rejected. A Qt integration test pairs two desktop workers,
compares their actual dialog codes and completes a transfer to a hidden window.
Lint also passed. Tests found and fixed shutdown ordering under active transfer.

Limitations: no independent security audit; physical Mac ↔ Windows acceptance
is unverified. Pairing interrupted during final commit may need repeating.
Multi-file publication is not a single filesystem transaction; a crash can
leave some complete files. Lost completion receipts are reported as failures.
Next: native packaging, executable smoke checks and CI.

## M5 — Packaging and installation

Added native PyInstaller builds, Windows portable ZIP, user-level install/remove
scripts, Apple Silicon app/ZIP/DMG scripts, bundled notices, reproducible version
constraints, rotating logs and frozen-startup diagnostics. The build excludes
unused Qt PDF/VirtualKeyboard/QML modules and unrelated host-native DLL paths.

Validation: **61 pytest tests passed**, lint passed, and the actual Windows
windowed executable passed `scripts/smoke_bundle.py` outside the checkout with
PYTHONPATH/PYTHONHOME cleared. Report: frozen=true, Qt 6.12.0 dialog passed,
mutual-TLS transfer complete, SHA-256 content match. Portable ZIP built locally
(approximately 42 MB). The first frozen run exposed an incompatible ICU DLL
from an unrelated host tool; sanitized build PATH fixed it before this commit.

Limitations: Windows portable bundle verified on this development host, not a
clean Windows VM. User-level installation is provided but not installed into the
developer's account. Mac build and DMG are pending CI or physical arm64 execution.
No publisher signing or notarization is claimed. Next: GitHub Actions and inspect
the actual run results.

M5 follow-up: the final packaging commit's tests passed but its shell continued
after an import-order lint failure. A separate corrective commit fixes the import
and adds `scripts/check.py`, which fails immediately on lint/format/test errors.
The complete gate was then rerun successfully (61 tests). This history is retained.

## M6 — GitHub and CI

Private repository created without replacing history:
`https://github.com/ovitch20051208-png/LanBridge`.
Each prior milestone and the M5 lint correction have been pushed separately.

Added pinned, read-only GitHub Actions for Windows x86-64 and macOS 15 arm64,
Python 3.12/3.13 test matrix, native packages, frozen executable checks and build
artifacts. Added developer/rollback instructions, change log and lean Qt Essentials
dependency configuration. No signing/publishing credentials are present.

Local validation at the CI configuration checkpoint: full 61-test suite and lint /
format gate. GitHub Actions execution is **pending** until the workflow is pushed
and its actual results are inspected. The final verification entry below will
record the observed result; workflow existence alone is not a passing run.
