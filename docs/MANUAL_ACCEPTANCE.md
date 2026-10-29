# Physical Mac ↔ Windows acceptance

M7 is in progress on a real M3 and Windows computer. See the [observed evidence](M7_ACCEPTANCE.md) for completed checks; the entire checklist below is not yet signed off.

Execution order is defined in the [roadmap](ROADMAP.md) / [中文阶段规划](ROADMAP.zh-CN.md):
M7 finishes functional/fault checks, M8 verifies clean installation and actual
login before freezing the baseline, M9 redesigns UI/UX on a separate branch and
repeats acceptance, and M10 validates signed distribution. The checklist below
remains the behavior contract across those stages.

Record build SHA, OS versions, CPU architecture, LAN topology, tester and date.
Use a Windows 11 x86-64 machine and a real Apple Silicon Mac. No browser is used.

## Setup and pairing

1. Install/run the native application on both computers. Allow inbound access
   on a trusted private LAN if the OS asks; do not disable the whole firewall.
2. Confirm both device names appear without entering an IP. Rename one device
   and restart; verify the same fingerprint remains, without duplicate entries.
3. On the recipient click **Allow pairing (2 min)**. On the sender select it and
   click **Pair device**. Compare all six code groups on both screens.
4. Decline once: neither device should become trusted. Repeat and choose
   **Codes match** on both. Restart both applications: trust must persist.
5. In Settings install the file-manager action on each computer. Close both
   main windows; tray/menu-bar receivers must remain available.

## Required release gate: Finder → Windows

1. In Finder select a normal file, a Unicode/space-named file and an empty file.
2. Right-click → Quick Actions/Services → **Send with LanBridge**.
3. Confirm the already-running instance shows recipient selection; no second
   unrelated instance stays running. With one paired online computer, the request starts directly; with several, click Windows in the compact recipient selector (no main-window Send files step).
4. Without manually opening Windows LanBridge, confirm a foreground dialog shows
   sender, the complete file list, total size and Accept/Decline.
5. Click **Accept**. Confirm progress and speed on both systems. Check files in
   the configured receive folder (new installations: Desktop/LanBridge Received) and compare SHA-256 values.
6. Verify both computers show completion only after validation. No website,
   cloud upload, manual IP, or receiver-side file selection should be involved.

## Reverse gate: Explorer → macOS

Repeat with Explorer → Show more options → Send to → **Send with LanBridge**.
The Mac must show the incoming dialog while its main window is hidden and save
accepted files automatically. Repeat all edge cases below in both directions.

For Wi-Fi interruption, identify the exact computer to disconnect first and keep
the control computer online. Agree a recovery interval (for example 45 seconds)
before disconnecting; reconnect without waiting for an offline chat notification.
Confirm actual payload bytes before the interruption, check error/cleanup, then
start a fresh request with receiver consent and verify the complete file hash.
Finished tasks can be archived to return to Ready; their session-history entries
remain reviewable. Archiving is separate from cancelling an active transfer.

## Edge cases

- Decline: sender sees Declined; no content/staging file remains at the receiver.
- Ignore request: timeout is clear; stale dialog disappears; no success.
- Select duplicate basenames from different folders: original files stay intact;
  received names gain numeric suffixes. Test an existing target file too.
- Transfer at least 4 GiB and multiple files: UI stays responsive; RAM does not
  grow in proportion to file size; hashes match.
- Cancel from either computer both while awaiting acceptance and during transfer.
- Disconnect Wi-Fi, quit receiver, or terminate it mid-transfer. Sender must fail
  clearly, never report success. Restart receiver and inspect staging cleanup.
- Forget a device: pending/active requests stop; future transfers require pairing.
- Start two Finder/Explorer actions quickly; inspect selected paths and task list.
- Restart login with launch-at-login enabled, then disable it and repeat login.
- Change the download directory; test unavailable/read-only locations and low disk.
- Disable multicast only: use **Connect manually** with the recipient's Settings
  address/ports. Pair and transfer still work. Re-enable normal discovery afterward.
- Test light/dark OS appearance and a non-administrator user.
- Uninstall integration: action disappears; user files/settings/downloads stay.

Windows: `Get-FileHash -Algorithm SHA256 -LiteralPath '<path>'`.
Mac: `shasum -a 256 -- '<path>'`.

## Three-physical-computer gate — M7 round 7E

This is required before the pre-UI/UX baseline, not deferred to visual redesign.
The planned topology is the existing Mac A, Windows B and an additional Windows C
reported available by the owner. C's Windows 11 x86-64 environment and exact build
are not yet verified. Detailed expectations are in the [roadmap](ROADMAP.md#m7-round-7e--three-computer-gate-before-uiux)
and [中文三机清单](ROADMAP.zh-CN.md).

- Use distinct identities on three real hosts. Record OS/build/architecture,
  fingerprint, app source SHA, receive folders and LAN. Discover two peers per
  machine; establish each necessary pair with the full six-group comparison.
- Verify A→B, B→A, A→C, C→A, B→C and C→B separately: explicit consent, both ends
  complete, exact hashes and no staging. Windows-to-Windows is included.
- With two paired online targets, invoke Finder/Send To and choose each target
  once in separate requests. Only that host is prompted. Cancel sends nothing;
  one eligible target still direct-sends. Recheck same display names with distinct
  identities, and exclude unpaired/offline/revoked candidates.
- Observe actual overlapping payload for A→B plus A→C, B→A plus C→A, and A↔B
  plus C→A. Validate individual prompts, correct task/progress/history ownership
  and output hashes. Mix large/small files and inspect UI responsiveness.
- Decline/cancel one task while the other continues. Disconnect/Quit B while
  A↔C continues; revoke B while C stays paired. Check peer-specific cancellation,
  failure and staging cleanup, then restore/re-pair/retry B.
- B/C concurrently send different same-basename contents to A with an existing
  sentinel. Preserve all contents without overwrite; validate by hash.
- Reopen/close main windows and repeat native entries with one normal-profile
  instance per host. Record request IDs and per-host observations; Windows clicks
  require tester confirmation. Three processes on one host are not this gate.

These are separate sends with per-request consent; no broadcast feature is
introduced. Repeat affected three-computer checks after UI/UX changes.

## Automated reproduction

```
python -m pytest -q
python scripts/two_peer_demo.py
python scripts/two_peer_demo.py --decline
python scripts/smoke_discovery.py
```

The two-process demo uses temporary independent identities, compares actual
pairing codes, transfers 12 MiB plus an empty file over mutual TLS and validates
SHA-256. Its automatic decisions exist only in the test harness. The desktop
application never auto-accepts files. These local checks do not certify the two
physical-platform gates above.
