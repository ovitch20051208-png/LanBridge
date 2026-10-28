# Physical Mac M7 captures — 2026-10-27

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
