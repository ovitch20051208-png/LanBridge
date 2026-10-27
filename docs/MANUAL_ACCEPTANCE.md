# Physical Mac ↔ Windows acceptance

M7 is in progress on a real M3 and Windows computer. See the [observed evidence](M7_ACCEPTANCE.md) for completed checks; the entire checklist below is not yet signed off.

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
