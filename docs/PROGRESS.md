# Verification record

M1–M6 development host: Windows x86-64, Python 3.12.10; a physical Mac was
unavailable at those checkpoints. M7 below records the subsequent real M3 work.
Earlier unavailable/unexecuted statements describe their historical checkpoints.
Milestone commits are individually recoverable in Git history. Current physical
evidence is summarized in [M7_ACCEPTANCE.md](M7_ACCEPTANCE.md).

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

## Bilingual documentation milestone — 2026-10-27

Replaced the short developer-first README with a user-first English README and
equivalent `README.zh-CN.md`. Both place English / Simplified Chinese navigation
at the top and link to complete, illustrated guides in `docs/USER_GUIDE*.md`.
The guides cover every current main-window, incoming-dialog, settings and tray
control, plus installation, first pairing, file-manager actions, manual endpoints,
cancellation, saved files and troubleshooting.

Added 11 actual Windows captures from isolated loopback fixtures, with provenance
in `docs/images/user-guide/README.md`. The accepted documentation transfer used
real pairing, mutual TLS and three files; received SHA-256 digests matched.
Pictures show the real English interface and do not claim Mac UI or physical
cross-platform acceptance. No production user profile or host LAN address was used.

Validation: `scripts/check.py` passed the documentation gate (13 Markdown files,
144 local links and 11 images), lint, formatting and **61 automated tests**.
The new `scripts/check_docs.py` is part of the normal gate, so missing translated
links, section anchors or image assets fail future checks. GitHub's GFM renderer
also rendered all four English/Chinese README/guide documents successfully for
an offline preview with embedded screenshots. Local-file browser automation is
blocked by the browser URL policy; the preview is delivered for the user to open.

Application behavior and desktop binaries are unchanged by this documentation
milestone. Native file-manager and physical Mac ↔ Windows acceptance remain the
next user testing steps described in the guide and manual acceptance checklist.

Documentation CI follow-up: source commit `98b18fa2099b17bfc3bb9567aa80599073848f0c`
passed [run 40580159815](https://github.com/ovitch20051208-png/LanBridge/actions/runs/40580159815).
All six Windows/macOS test and native build jobs completed successfully, including
the new documentation gate and both actual frozen-executable diagnostics. The
offline bilingual reader also passed static JavaScript syntax and embedded-content
checks: all four documents, 28 image references, and no external scripts. The
browser's local-file preview restriction was not bypassed.

## M7 — Physical Mac baseline — 2026-10-27

The checkout was clean and `git fetch origin main` confirmed both local and remote
main at `200b0831c1c1279a1c5ef0fa2b03c8ed51f9ac90`; no history was reset.
GitHub repository metadata now reports **public** (earlier entries describe its
previous private state). No applicable AGENTS.md was present.

Host: real **Apple M3**, **macOS 15.7 (24G222)**, native **arm64 Python 3.12.16**
installed with Homebrew; Command Line Tools were present. The default Python 3.13
was not used for packaging. Homebrew's initial post-install failed while reading
a newer formula; updating Homebrew and rerunning postinstall resolved it.

Installed `-c constraints.txt -e ".[dev]"` in `.venv`; `pip check` passed.
`scripts/check.py`: documentation links/images, Ruff lint/format, **60 passed,
1 Windows-only COM test skipped**. Both two-process demos passed (accepted 12 MiB
plus empty file with hashes checked; declined without downloads), and two live
mDNS advertisers discovered each other on this Mac. These remain local tests.

`sh scripts/build_macos.sh` produced an arm64 app, ZIP and DMG from the clean source
above. The frozen executable passed its outside-checkout Qt dialog / mutual-TLS /
SHA-256 diagnostic. BUILD-INFO reports `source_dirty=false`, Python 3.12.16,
Qt 6.12.0 and arm64. Baseline archive SHA-256:

- ZIP: `bfedc8f9190c4582c584156ff2d17d60a91c637d43b90d5e1df312f22f0be99e`
- DMG: `c542686c4a950eef4eef97f083a74155e9241a68a1948c754ee1b7734e80765e`

Copied the app to `/Applications/LanBridge.app`, opened its actual native window
and settings, saved a distinct device name/custom test receive directory, and
installed the Finder action from the app. Normal user state is used for this
physical flow; tests above used isolated temporary identities. No keys, tokens,
runtime configuration or build caches are committed.

Initial physical discovery found the Windows device, but pairing failed: its
advertisement included four link-local adapters plus a reachable LAN address;
`parse_peer` selected the first, unreachable link-local address. The timeout
displayed an empty `Could not pair:` message. Strict bundle signature validation
also found dangling QtSvg symlinks left by binary-only module filtering. These
are observed issues to repair next, not successful pairing/Finder transfer gates.
No physical two-computer file transfer has completed at this checkpoint.

M7 discovery correction: prefer non-link-local advertised IPv4 addresses over
APIPA addresses regardless of DNS order, while retaining link-local-only peers.
The actual Windows LAN endpoint was reachable on both advertised ports. Added
regression coverage for adapter ordering and a useful pairing timeout message;
`scripts/check.py` passed: **64 passed, 1 skipped**, documentation/lint/format
passed. Physical pairing will be retried with the rebuilt native application.

M7 packaging correction: apply unused-Qt filtering to data/symlink entries as
well as binaries, including each symlink target. The rebuilt app has no dangling
links and now passes `codesign --verify --deep --strict`; that validation and a
broken-link check run before every Mac archive build. Recorded macOS-only
`macholib==1.16.4` in the dependency constraints. Full gate: **64 passed, 1 skipped**;
arm64 app/ZIP/DMG build and actual frozen Qt/TLS/hash diagnostic passed again.
This validates the ad-hoc signature's integrity, not Developer ID or notarization.

M7 usability correction: the tester could not recognize **Allow pairing (2 min)**
as clickable. The previous rounded-button stylesheet left secondary actions
looking like plain text. Added visible, palette-based button borders/backgrounds
and a distinct disabled primary-button appearance. Full gate remains **64 passed,
1 skipped**; native visual verification follows in the next build.

M7 background prompt adjustment: during the first reverse physical request the
computer-control tool captured the hidden parent as a blank window and could not
access its sheet. The tester subsequently confirmed clicking Accept on the Mac;
an empty test file was saved, with the expected empty-file SHA-256 and no staging
directories. Therefore this is **not evidence that the app failed to display a
prompt to the user**. Use asynchronous application-modal standalone dialogs
instead of window-modal sheets, so background prompts do not depend on a visible
main window. Consent and pairing still require explicit decisions. Strengthened
the hidden-recipient integration check to verify dialog exposure while the main
window stays unexposed. Full offscreen gate: **64 passed, 1 skipped**; the complete
desktop test module also passed with the native Cocoa plugin (**12 passed**).

M7 destination update requested by the tester: new installations now default to
the OS Desktop's `LanBridge Received` folder on both platforms. Saved destinations
remain unchanged. Settings Save creates a newly entered destination; Received
Files creates the configured folder before opening it. Added settings guidance
and matching English/Chinese documentation. Isolated regression tests verify the
new-user default, folder creation, custom-path persistence and preservation of
an existing Downloads setting. Full gate: **66 passed, 1 skipped**; native Cocoa
desktop tests: **14 passed**. This is not a clean-system installation result.

M7 physical small-file phase: real Finder → Windows transfer of 37 B completed
on both sides (Windows reported by tester). Actual Finder multi-selection then
sent three files (78 B total: text, empty and Chinese/space-named) to the tester's
chosen Windows Desktop folder; sender received validation receipts. An explicit
Windows Decline produced **declined, 0/78 B**. A repeated accepted batch also
completed; collision-suffixed names still need direct confirmation.

The tester sent the original three files back from Windows. With the Mac main
window hidden, the operator observed the standalone Incoming files dialog and
clicked Accept. Both sides reported complete (`3eaf4370…`, Windows via tester).
All received SHA-256 values matched the original Mac sources; no Mac staging
directories remained. Real Finder normal-profile IPC retained the same primary
PID and left no unrelated second app process. Mac trust/fingerprint survived
app replacement/restart. Full evidence and screenshots are in
[M7_ACCEPTANCE.md](M7_ACCEPTANCE.md), with explicit unverified items.

In native Settings, Browse → Desktop → New Folder → Create → Open → Save created
and selected Desktop/LanBridge Received. Login registration was enabled, its
valid LaunchAgent path/arguments checked, then disabled and removal verified;
actual logout/login remains untested. The clean `cac55f8` DMG passed checksum,
read-only mount, strict app signature and actual mounted frozen Qt/TLS/hash
diagnostic. No clean-system, Developer ID or notarization result is claimed.

M7 physical large-file/interruption phase (`cac55f8` app): **4 GiB completed in
both directions**, average UI rates 26.4 MiB/s Mac → Windows and 36.4 MiB/s
Windows → Mac. The reverse transfer came from the actual Windows Send To action
after first-time installation; the initial preview still required Send files in
its main window. Received bytes (4,294,967,296) and SHA-256 matched the original
Mac source. Mac RSS peaks were 130.31 MiB sending and 81.59 MiB receiving; these
are observations of this run, not a general performance claim.

Sender cancellation while awaiting consent and during payload showed cancelled.
The tester confirmed no Windows remnants after payload cancellation. Quitting
the Windows receiver during payload produced **error: Connection lost** on Mac,
never success; restarting Windows preserved Paired and the tester reported no
residual files. Native Finder removal/reinstallation was verified by actual menu
absence/reappearance; menu-bar Received Files opened the chosen Desktop folder.
Light appearance was inspected and original Auto restored. `security find-identity`
found zero signing identities; notarytool is present, signing/notarization remain
unperformed. Evidence and actual screenshots are in M7_ACCEPTANCE.md.

CI for `212af5b`: [run 40587559371](https://github.com/ovitch20051208-png/LanBridge/actions/runs/40587559371)
completed successfully in all six jobs. Python 3.12 logs were inspected: Windows
**67 passed**, Mac **66 passed, 1 skipped**, docs/lint/format passed; both native
builds and frozen executable diagnostics passed. Later interaction improvements
requested by the tester are a separate implementation phase.

M7 interaction refinement requested during physical testing: authenticated IPC
now preserves an explicit `--send` intent separately from ordinary file
selection. A sole paired online recipient receives the request directly; with
multiple recipients, one click in a compact picker sends it. Startup briefly
collects discovery, queued actions retain separate path lists, and no paired
online target means no automatic send. Existing certificate pins, pairing and
per-request receiver consent remain unchanged. Settings now persistently shows
action installation state and offers Reinstall, which updates the same fixed
shortcut/workflow rather than downloading another app.

Implementation validation: full gate **74 passed, 1 skipped**; native Cocoa
desktop/IPC/integration checks **25 passed, 1 skipped**. Tests include actual
cross-process IPC intent forwarding, real paired TLS delivery with a hidden
sender and explicit receiver consent, multiple-target one-click selection,
unpaired/offline/revoked targets, empty selections and repeated native action
installation. Rebuilt-bundle and physical direct-send checks follow separately.

The clean `7af38d6` arm64 bundle passed strict signature and frozen Qt/TLS/hash
checks. Physical Finder **cold-start direct send** completed (`7fd9f2dd…`, 37 B):
the app was not running, Finder launched it with --send, and Windows received its
request without a main-window Send files click. A second real Finder action sent
a Chinese/space-named file through the existing PID 34896 (`65de2700…`, 41 B),
also complete without Send files. Windows acceptance/receipt was reported by the
tester; both completions were observed on Mac. Reinstall showed the persistent
Installed state, updated the same sole workflow and retained one app process.

Native screenshot QA found the expanded settings form could compress its wrapped
directory hint. Widened the form and reserved font-scaled hint height. The full
gate after this layout adjustment remained **74 passed, 1 skipped**; rebuilt
visual verification is recorded next rather than inferred from the tests.

## M7 continuation — application reopening — 2026-10-28

The installed `6bccb65` Mac app was still running and listening after the night,
but double-clicking its actual Applications icon did not restore the hidden
window. Finder's selected Desktop item named LanBridge was separately confirmed
to be the source folder, not the application.

Added an explicit native macOS reopen AppleEvent handler, using OS frameworks
and the standard library, so a user opening the app raises its existing window.
It handles only reopen events, preserving background startup, incoming dialogs
and file-manager direct-send behavior. The same shared open-request handler now
handles a second Windows EXE launch and preserves previous file selection on
both platforms without sending those files. The user requested cross-platform
feature parity and publishing each completed module separately.

Module checks: full gate **76 passed, 1 skipped**; native Cocoa reopening,
file-manager and desktop modules **23 passed**. The native handler callback and
cleanup were exercised on this Mac; frozen Finder double-click verification
follows after rebuilding rather than being inferred from these checks.

Frozen double-click testing found that registering before `app.exec()` was too
early: AppKit installs its default AppleEvent handlers during launch, replacing
the handler. Registration now runs on the first event-loop turn, after those
defaults. The full gate remains **76 passed, 1 skipped**. This correction requires
another frozen Finder check; the earlier callback-only test did not exercise
AppKit startup ordering.

Clean `f530938` frozen Finder verification passed: closing then double-clicking
`/Applications/LanBridge.app` restored the main window; repeated with a selected
file and with a minimized window. Selection remained without sending, and PID
42873 stayed unchanged. Background listener remained available. Actual Windows
`6bccb65` Send To direct send was then accepted on the hidden Mac (`766beab7…`,
37 B), completed and saved as `(2)` without overwriting the original or the
different `(1)` sentinel. All hashes and staging cleanup passed on Mac; the tester confirmed Windows also displayed complete. Screenshot evidence is 22–24.

Cross-platform behavior is shared: Desktop receive-folder default and custom
folder creation/selection, one-recipient direct send/multi-recipient selection,
persistent install state and reinstall feedback, visible buttons/dialogs and
existing-window reopening. Finder/Send To, menu-bar/tray and login registration
use their respective native implementations. `c863854` CI passed all six jobs;
Windows/macOS Python 3.12 logs each show **76 passed, 1 platform-specific skip**.

`f530938` CI run 40667054324 also completed all six jobs successfully.
