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

## Final observed verification — 2026-10-27

**All six implementation milestones are committed and pushed.** The entries above
record their checkpoint states; this section is the current verification result.

Code/build source: `b17d388207526dc843b331d578f30928d320812a`.
[GitHub Actions run 40571919800](https://github.com/ovitch20051208-png/LanBridge/actions/runs/40571919800)
finished **successfully**. All six jobs and artifact uploads were inspected:

| Job | Observed result |
| --- | --- |
| Windows x86-64 / Python 3.12 | 61 passed; lint and formatting passed |
| Windows x86-64 / Python 3.13 | 61 passed; lint and formatting passed |
| macOS 15 arm64 / Python 3.12 | 60 passed, 1 Windows COM test skipped; lint/format passed |
| macOS 15 arm64 / Python 3.13 | 60 passed, 1 Windows COM test skipped; lint/format passed |
| Windows native build | Portable ZIP built, actual frozen Qt/TLS diagnostic passed, artifact uploaded |
| macOS native build | arm64 .app, ZIP and DMG built, actual frozen Qt/TLS diagnostic passed, artifact uploaded |

The Mac build's Mach-O CPU type, Bonjour metadata and clean source build manifest
were independently inspected after download. The artifact ZIP digest matched
GitHub's reported SHA-256. No Developer ID signature or notarization is claimed.
The local Windows bundle was also rebuilt from a clean checkout of the same code
commit using a fresh Essentials-only environment and passed the frozen diagnostic
outside the source tree. Native Windows widget rendering was inspected.

Delivered packages in the enclosing `outputs/` folder:

| File | Origin | SHA-256 |
| --- | --- | --- |
| LanBridge-windows-x86_64-0.1.0.zip | Local Windows clean build, Python 3.12.10 | `3d41ddbda6c0f0563ceb1e5832883fa7ce6260d2a9d7d34b50f9cb3003671402` |
| LanBridge-macos-arm64-0.1.0.dmg | Verified macOS CI build | `8ec83fa6a2671f472bbed300e6c7f7da60daa3b4198d5c4c1b22a9c7d8b1a2fd` |
| LanBridge-macos-arm64-0.1.0.zip | Verified macOS CI build | `4db4d082dfd6745196f1ec961e5bd4fb334d5f27471eb85c2c5cf8faf66642b8` |

`SHA256SUMS.txt` accompanies them. Generated packages, runtime state, certificates,
private keys and caches are excluded from the Git source history. GitHub remains
private; no force-push or history replacement was used. The final documentation
commit only records this evidence and does not change the tested application.

### Commit index

| Milestone | Commit |
| --- | --- |
| M1 P2P core | `fee312f` |
| M2 desktop / discovery | `f517264` |
| M3 native integration / IPC | `68b8f26` |
| M4 security / reliability | `35a84f6` |
| M5 native packaging | `3fa2c2e` |
| M5 check-gate correction | `d0966ac` |
| M6 GitHub CI / native artifacts | `b17d388` |

### Remaining release gates

Physical Mac M3 ↔ Windows 11 transfers using real Finder/Explorer actions have
**not** been performed. The macOS CI runner validates arm64 code and packaging,
not that physical two-machine interaction. Complete MANUAL_ACCEPTANCE.md,
clean-machine install/login-startup checks, publisher signing/notarization and
dependency license review before calling this a production release. V1.0 resume,
folders and auto-accept remain intentionally absent. These limits are not
presented as completed acceptance tests.
