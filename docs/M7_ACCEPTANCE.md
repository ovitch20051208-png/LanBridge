# M7 physical Mac and two-computer evidence

Dates: 2026-10-27–28. Mac operated through native UI automation; Windows operated by
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
- Core large-transfer app/ZIP/DMG checkpoint: `cac55f8`, `source_dirty=false`, arm64, Python 3.12.16,
  Qt 6.12.0. Strict deep ad-hoc signature verification passed. DMG checksum,
  read-only mounting, mounted app signature and actual mounted executable's
  Qt/TLS/SHA-256 diagnostic all passed. This is not Developer ID signing or
  notarization, and is not a clean-system install.

| Local package | SHA-256 |
| --- | --- |
| arm64 ZIP | `4c493f12eb60fe0d6d0a83334454c82e540f2a2b371f02395637b0fee137e113` |
| arm64 DMG | `869492a54a209920ca7a18aa19811baed3db4f9dd81db014ad7b48c83b016670` |

The table above identifies the core large-transfer checkpoint. The direct-send
refinement was built cleanly at `7af38d6`; the subsequent settings-layout bundle
is `6bccb65`, also `source_dirty=false`, arm64/Python 3.12.16/Qt 6.12.0 and passed
strict signature verification and its actual frozen diagnostic. Local
package hashes at `6bccb65`:

- ZIP: `536e1b5154a1bdb9128313b3ada53acc1e855b5cc5073478e165d957d649dce0`
- DMG: `66912b189807e49235868f840fc6f090b16a7041a087f87be28c10a0daf2f763`

The application-reopen correction is built cleanly at `f530938`, with the same
native arm64/Python/Qt environment, strict signature verification and frozen
diagnostic passing. Current local package hashes:

- ZIP: `f381fbd743426872f0df3a62a380a7427e68b7dfeb92897605f0092afac80d58`
- DMG: `dfc990e90867fa8f45619d721e657e0934097efc82b62347fc7142cd3d6f5810`

Windows was updated by the tester to the CI-built `6bccb65` portable package.
Its inner ZIP SHA-256 is
`1e839c29755236105886a050a2a94d6f7748416993a84cf1652999d233522591`.
The old preview's exact build remains unknown; it was used for the earlier large
transfer checks.

The final Windows `f530938` package was separately downloaded from successful
CI run 40667054324 and verified before LAN delivery. Inner ZIP: 41,940,973 bytes,
SHA-256 `8850d2bc81722a8a1153a42252b46ec00f4423c814e24a70b66ae9754b59be9a`,
`source_dirty=false`, AMD64/Python 3.12.10/Qt 6.12.0. It was renamed locally to
`LanBridge-Windows-f530938.zip` for unambiguous receipt; its bytes are unchanged.

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
| New Finder cold-start direct send | Clean `7af38d6` app initially stopped; real Finder action launched --send and issued a 37 B request to the sole paired online Windows peer, with no main-window Send files click. Tester accepted; Mac completion `7fd9f2dd…` observed afterward. |
| New Finder existing-instance direct send | Real Finder action on a Chinese/space-named 41 B file forwarded send intent to the same PID 34896, issued the request directly, and completed (`65de2700…`). Tester confirmed receipt; no extra app process remained. |
| Persistent install state | Actual Settings showed Installed, its action path and Reinstall. Reinstall showed explicit no-download feedback and retained one workflow containing only Info.plist/document.wflow. The `6bccb65` form was visually rechecked with a readable full receive path, fingerprint and hint. |


| Mac application reopening | Clean `f530938`: close the main window, double-click the actual `/Applications/LanBridge.app` icon in Finder, and the same window returns. Repeated with a selected file, then with a minimized window: selection remains and no send starts. PID stayed 42873; listener stayed available while hidden. Screenshot 22 records the restored window, not the hidden interval. |
| Windows right-click direct send | Tester reinstalled the action from `6bccb65` and invoked Send To without clicking Send files. On retry, operator observed the standalone Mac consent dialog with the main window hidden, clicked Accept, then observed request `766beab7…` complete at 37/37 B. Initial attempt timed out awaiting Mac consent and is not counted as a completed transfer. Tester also confirmed Windows displayed complete. |
| Reopen fix / Finder regression | Quit `f530938` normally and verified no app process remained. Actual Finder Send with LanBridge on the 40 MiB updated Windows ZIP cold-started PID 43135 with --send and sent directly, without a main-window Send files action. Request `8460e6f4…` completed on Mac; tester confirmed receipt on Windows. Later double-clicking the Applications icon restored the same process window. |
| Physical collision protection | The direct-send retry saved `01 Mac hello (2).txt`, 37 B, matching the original SHA-256. Hashes of the existing original and deliberately different `(1)` sentinel were unchanged; no `.lanbridge-*` staging directory remained. |

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

Latest full Mac gate: documentation, lint/format, **76 passed, 1 Windows COM test
skipped**. Native Cocoa reopening/file-manager/desktop modules: **23 passed**.
The `c863854` CI completed all six jobs successfully, including both native
builds and frozen diagnostics. Inspected Python 3.12 logs: Windows **76 passed,
1 native macOS test skipped**; Mac **76 passed, 1 Windows COM test skipped**.
The startup-order follow-up `f530938` CI also completed all six jobs successfully; its Python 3.12 logs each show **76 passed, 1 platform-specific skip**.
The right-click tests cover explicit authenticated IPC send intent, single/multi
recipient dispatch, unpaired/offline/revoked targets, empty selections and actual
paired TLS consent without opening the sender main window. Isolated two-process accept
and decline demos and multicast smoke check passed. Actual frozen diagnostics
also passed outside the checkout and from the mounted DMG. These use temporary
identities/configuration and do not replace the physical checks above.

## Remaining checks and one observed runtime log issue

- Fresh non-administrator/clean-system installation, downloaded-app quarantine
  prompts and actual logout/login have not been exercised. Login registration
  toggling was exercised; the setting was restored to disabled.
- Developer ID/notarization and Windows publisher signing remain unperformed.
  This Mac has no valid signing identity; notarytool is available.
- Three-physical-computer recipient selection, first-pairing Decline/revocation,
  Wi-Fi toggling, receiver force-kill/restart cleanup, low disk/read-only receive
  folders and the full manual edge-case checklist are not yet signed off.
- At 21:37 UTC during forced Windows receiver Quit, one non-fatal asyncio
  `_call_connection_lost` traceback was logged after the correct Connection lost
  UI error. Subsequent real transfers succeeded and cleanup was reported by the
  tester. Its signature resembles a reported [CPython duplicate-teardown issue](https://github.com/python/cpython/issues/156512),
  but this host's exact trigger has not been independently isolated; no runtime
  monkeypatch or exception suppression was applied.

See [PROGRESS](PROGRESS.md) for checkpoint commits and CI, and
[MANUAL_ACCEPTANCE](MANUAL_ACCEPTANCE.md) for the remaining full release checklist.
