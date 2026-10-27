# M7 physical Mac and two-computer evidence

Date: 2026-10-27. Mac operated through native UI automation; Windows operated by
the project owner and reported in chat. Windows screenshots/control are not
available to the Mac operator. This record distinguishes observed Mac results
from the tester's Windows reports; the complete manual release gate is not yet
finished.

## Environment and builds

- Real Apple M3; macOS 15.7 (24G222); native arm64 Python 3.12.16 in `.venv`.
- Existing Windows 11 x86-64 development-preview app. Its exact local build
  manifest and OS build number have not been supplied.
- Reachable local LAN, direct mDNS discovery and TCP between the computers.
  No manual IP was needed for successful desktop transfers.
- First Mac transfer: clean `e8cd2d7` app; subsequent destination/UI checks:
  clean `cac55f8` app. Both run at `/Applications/LanBridge.app`.
- Latest local app/ZIP/DMG: `cac55f8`, `source_dirty=false`, arm64, Python 3.12.16,
  Qt 6.12.0. Strict deep ad-hoc signature verification passed. DMG checksum,
  read-only mounting, mounted app signature and actual mounted executable's
  Qt/TLS/SHA-256 diagnostic all passed. This is not Developer ID signing or
  notarization, and is not a clean-system install.

| Local package | SHA-256 |
| --- | --- |
| arm64 ZIP | `4c493f12eb60fe0d6d0a83334454c82e540f2a2b371f02395637b0fee137e113` |
| arm64 DMG | `869492a54a209920ca7a18aa19811baed3db4f9dd81db014ad7b48c83b016670` |

## Observed physical checks

| Check | Evidence / scope |
| --- | --- |
| Discovery | Real Windows peer appeared on Mac. Initial APIPA address selection failed; corrected address preference allowed pairing. |
| Pairing | Tester confirmed comparing all six groups and clicking Codes match on both computers; both displayed Paired. Mac operator observed saved trust. First-pairing Decline has not been independently rechecked. |
| Mac restart / identity | Replaced/restarted the Mac app; fingerprint and trusted Windows identity persisted. |
| Finder single file | Selected the real test file in Finder → actual Send with LanBridge service → existing window received the file. Primary PID stayed 30898, no second LanBridge process remained. |
| First Mac → Windows | Request `46020ec1…`: 37 B; Mac displayed complete after its validated receipt. Tester reported Accept, complete and automatic saving. |
| Finder multi-selection | Real Finder selected three files in a Chinese/space-named directory. The existing normal-profile process received all three names; no isolated test profile was substituted. |
| Mac → Windows desktop folder | Request `08de1308…`: three files, 78 B, complete on Mac. Tester confirmed all three appeared in the selected Windows Desktop folder. |
| Repeated batch | Request `4e0f5339…`: three files, 78 B, complete. Tester accepted again; exact collision-suffixed filenames have not yet been independently inspected. |
| Decline | Request `cf2aeb6e…`: tester chose Decline; Mac displayed declined, 0/78 B. Tester reported that accepted files existed and refused files were not retained. Windows hidden staging cleanup remains based on that report, not direct filesystem inspection. |
| First Windows → hidden Mac | Tester accepted the Mac prompt for an empty test file. Mac filesystem contained the 0-byte file with the standard empty SHA-256 and no staging directory. Windows completion for this request was not independently observed. |
| Three-file Windows → hidden Mac | Request `3eaf4370…`: the operator observed the standalone Incoming files dialog while the main window was hidden and clicked Accept. Mac displayed receive complete, 78/78 B; tester confirmed Windows complete. All three files in the Mac Desktop folder matched the original source SHA-256, completing an actual Mac → Windows → Mac round trip. No staging directories remained. |
| Desktop folder selection | In the actual Mac app: Settings → Browse → Desktop → New Folder → Create → Open → Save. Saved path is Desktop/LanBridge Received. |
| Login setting | Enabled via real settings, verified valid LaunchAgent with the fixed app path and --background, disabled via settings, verified removal and saved false. Actual logout/login remains pending. |
| Window close vs Quit | Closing the Mac main window preserved its TCP listener/process; normal Quit removed the process before replacement. Menu-bar Received Files was exercised with tester assistance below. |
| Menu-bar Received Files | Tester clicked the Mac menu item; operator then observed Finder open Desktop/LanBridge Received with the actual received test files. |
| Finder removal / reinstall | Operator clicked Remove action in native Settings; workflow disappeared from disk and Send with LanBridge disappeared from the real Finder context menu. Reinstall restored both. The running transfer continued while settings remained responsive. |
| 4 GiB Mac → Windows | Request `d8dea1cc…`: actual Finder invocation, progress and speed observed, completed at 4/4 GiB with a validated receipt, average 26.4 MiB/s. Tester confirmed complete receipt on Windows. |
| Mac memory during 4 GiB send | 168 one-second RSS samples over 169.48 s (includes request/decision time): start 62.86 MiB, peak 130.31 MiB, final 58.66 MiB. This measures this Mac run, not Windows memory or a general throughput guarantee. |
| Cancel while waiting | Request `2bebbf3a…`: operator cancelled on Mac while waiting for acceptance; task became cancelled with no payload progress. Windows dialog disappearance was not independently observed. |
| Cancel during payload | Request `7f8a3b33…`: payload progress observed past 484.5 MiB, then operator cancelled at approximately 13%; task became cancelled. Tester confirmed no Windows remnants after cancellation. |
| Receiver Quit during payload | Request `410facac…`: tester accepted, then quit Windows from its tray. Mac showed error: Connection lost at approximately 9%, never complete. Tester restarted Windows, confirmed Paired persisted and no interrupted-transfer remnants remained. |
| Appearance | Native light appearance inspected alongside the dark screenshots; OS appearance was restored to its original Auto setting. |
| 4 GiB Windows → hidden Mac | Tester installed the actual Windows Send To action, invoked it from Explorer and clicked Send files in the existing preview app. Operator accepted the standalone Mac prompt with main window hidden. Request `e6f5b3f1…` completed at 4/4 GiB, UI average 36.4 MiB/s; received SHA-256 matched the original Mac source exactly, with no Mac staging leftovers. Tester confirmed Windows finished sending. |
| Mac memory during reverse send | 500 one-second RSS samples, including setup and waiting: peak 81.59 MiB, final 36.77 MiB. The 506.26 s sampling window includes installation/user setup time and is not the payload duration. |

![Finder selection on the real Mac](images/mac-m7/02-finder-selection.jpg)

![Multiple files ready through the real Finder entry](images/mac-m7/06-multiple-files-ready.jpg)

![Physical multiple-file sender completion](images/mac-m7/07-multiple-send-complete.jpg)

![Physical declined request with zero bytes transferred](images/mac-m7/08-send-declined.jpg)

![Mac consent with main window hidden](images/mac-m7/09-background-incoming.jpg)

![Mac receive completion for the three-file round trip](images/mac-m7/10-receive-complete.jpg)

![Actual 4 GiB transfer progress](images/mac-m7/12-large-progress.jpg)

![Actual 4 GiB sender completion](images/mac-m7/13-large-send-complete.jpg)

![Real payload cancellation](images/mac-m7/14-send-cancelled.jpg)

![Receiver Quit reported as Connection lost](images/mac-m7/16-receiver-quit-error.jpg)

![Explorer-originated large offer on a hidden Mac](images/mac-m7/17-large-background-incoming.jpg)

![4 GiB reverse receive complete](images/mac-m7/18-large-receive-complete.jpg)

## Generated small-file reference hashes

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `01 Mac hello.txt` | 37 | `4877bb69a9a4b2443be1dab75950cbc958e36760b378c415b2c2f7b7d3430a1b` |
| `中文 文件.txt` | 41 | `8e86973ec5151c3a279ea0ab8acb1a195e8783f6bc9884444a9fe73a1dbefdf0` |
| `empty.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `large 4 GiB.bin` | 4,294,967,296 | `8479e43911dc45e89f934fe48d01297e16f51d17aa561d4d1c216b1ae0fcddca` |

## Automated checks

Latest full Mac gate: documentation, lint/format, **66 passed, 1 Windows COM test
skipped**. Native Cocoa desktop module: **14 passed**. Isolated two-process accept
and decline demos and multicast smoke check passed. Actual frozen diagnostics
also passed outside the checkout and from the mounted DMG. These use temporary
identities/configuration and do not replace the physical checks above.

See [PROGRESS](PROGRESS.md) for checkpoint commits and CI, and
[MANUAL_ACCEPTANCE](MANUAL_ACCEPTANCE.md) for the remaining full release checklist.
