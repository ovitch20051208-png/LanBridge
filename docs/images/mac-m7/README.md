# Physical Mac M7 captures — 2026-10-27–28

These JPEGs are unedited captures of the real application/Finder on an Apple M3,
macOS 15.7 (24G222), captured with native computer-control screenshots. The app
runs from `/Applications/LanBridge.app` with the normal user's configuration.
Only generated test files are shown; no private keys, IPC tokens or private file
contents are included. Fingerprints are public device identifiers.

- `01-main-window.jpg`: physical Windows peer discovered before pairing.
- `02-finder-selection.jpg`: actual Finder selection in a Unicode/space-named
  directory. The screenshot captures the Finder window, not its context menu;
  the actual **Send with LanBridge** menu invocation was observed separately.
- `03-finder-file-ready.jpg`: Finder's file forwarded into the existing instance.
- `04-send-complete.jpg`: first physical Finder → Windows transfer, 37 B,
  receiver-validation receipt received. Windows Accept/completion was reported
  by the tester; this image is the observed Mac sender.
- `05-settings.jpg`: new settings UI, chosen Desktop receive folder and login
  startup unchecked (saved immediately afterward).
- `06-multiple-files-ready.jpg`: three real Finder-selected files in the existing
  app, including empty and Unicode/space-named files, with visible button borders.
- `07-multiple-send-complete.jpg`: physical three-file completion to Windows.
- `08-send-declined.jpg`: physical Windows Decline; sender remained at 0/78 B.
- `09-background-incoming.jpg`: actual Windows offer shown in a standalone Mac
  dialog with the main window hidden; the operator then clicked Accept.
- `10-receive-complete.jpg`: physical three-file reverse transfer complete; all
  received hashes matched the original Mac sources.
- `11-received-folder.jpg`: actual Finder directory opened by menu-bar Received
  Files (tester clicked the item; operator observed the result).
- `12-large-progress.jpg` / `13-large-send-complete.jpg`: physical 4 GiB send
  progress and validated completion to Windows.
- `14-send-cancelled.jpg`: physical sender cancellation during payload.
- `15-light-appearance.jpg`: real native light appearance; the original Auto
  system setting was restored afterward.
- `16-receiver-quit-error.jpg`: physical Windows receiver Quit caused Connection
  lost on the Mac sender, without a success state.
- `17-large-background-incoming.jpg` / `18-large-receive-complete.jpg`: physical
  Windows Send To entry → existing app → Mac consent → 4 GiB reverse completion.
- `19-direct-send-complete.jpg`: real Finder cold-start direct send completed
  without opening the sender main window or clicking Send files.
- `20-integration-status.jpg`: final expanded settings form, complete paths,
  persistent Installed state and Reinstall button.
- `21-warm-direct-send-complete.jpg`: Chinese/space-named file directly requested
  through the existing process, with no main-window Send files action.

Images 01–04 use the clean `e8cd2d7` Mac build. Images 05–06 use the clean
`cac55f8` build, as do 07–18. Both use native arm64 Python 3.12.16 / Qt 6.12.0. Older pictures
retain their original button appearance as evidence of the first transfer.
Screenshot speeds for tiny files include protocol/finalization latency; they are
not network throughput benchmarks. Addresses, paths and device identifiers are
specific to this test and must not be copied into another installation.

Images 19 and 21 use clean `7af38d6`; image 20 uses the clean `6bccb65` layout
correction. The initial 01–18 capture the earlier preview behavior; the file-manager
flow subsequently changed to direct send at the tester's request.

See [the verification record](../../PROGRESS.md) and
[physical acceptance checklist](../../MANUAL_ACCEPTANCE.md) for scope and limits.

Images 22–24 were captured on 2026-10-28 with clean `f530938`:

- `22-reopened-window.jpg`: actual Finder double-click restored the existing
  hidden window with the selected filename retained and no transfer started.
- `23-windows-direct-incoming.jpg`: real Windows `6bccb65` Send To direct offer;
  Mac main window was hidden and operator subsequently clicked Accept.
- `24-windows-direct-complete.jpg`: observed receive completion for that offer.
  Separate filesystem hash checks confirmed collision suffix `(2)`, unchanged
  existing files and no staging leftovers.

- `25-post-crash-recovery.jpg`: same clean `f530938`, after intentional receiver
  SIGKILL during a real 4 GiB stream and automatic staging cleanup on restart.
  A new physical Windows right-click offer completed on this Mac; tester also
  confirmed Windows complete. The peer remained Online/Paired.

Images 26–27 use clean `597e8a3` on the same M3:

- `26-edit-file-selection.jpg`: selected the Chinese-named entry in the real
  multi-select send list; Remove selected is enabled.
- `27-remaining-files-complete.jpg`: after removing that entry, only hello/empty
  remain and their 37 B physical transfer completed; Windows tester confirmed
  exactly those two incoming files and receipt. Source-file hashes were unchanged.

Images 28–30 use clean `597e8a3` on 2026-10-28 for physical Windows receiver
Wi-Fi interruption/recovery:

- `28-network-outage-progress.jpg`: actual payload progress (74.0 MiB); the
  immediately following AX observation recorded 74.5 MiB.
- `29-network-outage-error.jpg`: Mac sender failed with Broken pipe at about 2%
  after the tester disabled Windows Wi-Fi, never reporting complete.
- `30-network-retry-complete.jpg`: same file fully retransmitted after Wi-Fi was
  restored, without restarting/re-pairing. Windows tester also confirmed receipt.

- `31-empty-timeout-error.jpg`: unfixed clean `597e8a3`, after Windows sender
  Wi-Fi interruption. Empty error reason and zeroed count were observed despite
  83,214,336 actual staged bytes; automatic cleanup and file preservation passed.

Images 32–34 use clean `ec981af` for the corrected physical reverse Wi-Fi test:

- `32-timeout-failed-fixed.jpg`: explicit timeout message, Failed bar label,
  preserved 203.6 MiB count and available Archive task button.
- `33-task-archived-ready.jpg`: after actual Archive task, Ready is restored and
  the bar is hidden; running receive service stays available.
- `34-archived-history-review.jpg`: operator selected the Archived failure from
  the real history popup and reviewed the original error/byte details again.
  Windows Failed/archive/Ready behavior was separately confirmed by the tester.
