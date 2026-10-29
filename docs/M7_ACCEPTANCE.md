# M7 physical Mac and two-computer evidence

Dates: 2026-10-27–29. Mac operated through native UI automation; Windows operated by
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
diagnostic passing. Package hashes for this checkpoint:

- ZIP: `f381fbd743426872f0df3a62a380a7427e68b7dfeb92897605f0092afac80d58`
- DMG: `dfc990e90867fa8f45619d721e657e0934097efc82b62347fc7142cd3d6f5810`

Windows was updated by the tester to the CI-built `6bccb65` portable package.
Its inner ZIP SHA-256 is
`1e839c29755236105886a050a2a94d6f7748416993a84cf1652999d233522591`.
The old preview's exact build remains unknown; it was used for the earlier large
transfer checks.

The Windows reopening-checkpoint `f530938` package was separately downloaded from successful
CI run 40667054324 and verified before LAN delivery. Inner ZIP: 41,940,973 bytes,
SHA-256 `8850d2bc81722a8a1153a42252b46ec00f4423c814e24a70b66ae9754b59be9a`,
`source_dirty=false`, AMD64/Python 3.12.10/Qt 6.12.0. It was renamed locally to
`LanBridge-Windows-f530938.zip` for unambiguous receipt; its bytes are unchanged.

Editable file-selection build: clean `597e8a3`, arm64/Python 3.12.16/Qt 6.12.0,
strict signature and frozen diagnostic passed. ZIP SHA-256
`8d56ff0a2e13971922b59fbe06d2c93f474a6a211a663580566d549bca92704a`;
DMG `aed61da36dd3559ebdea519dd06b7bed247da5ff5046f1ae99195a7da0735ad3`.

The editable-selection Windows `597e8a3` package from CI run 40669476207 was
verified and delivered for physical validation as `LanBridge-Windows-597e8a3.zip`:
41,941,100 bytes, SHA-256
`1dab09ba17df272a01760c17d707016379fcb1e9784eac1de6573a06959e2cc9`,
`source_dirty=false`, AMD64/Python 3.12.10/Qt 6.12.0.

Timeout/terminal-history checkpoint: clean `ec981af` Mac bundle, native arm64
Python 3.12.16/Qt 6.12.0, strict deep signature verification and frozen diagnostic
passed. ZIP SHA-256 `46603f00ba50cbf21ddad3ec6f52fb21b458ef861e63a8f9662cfa9c161ed016`;
DMG `2b00d61dea37ae5f93a9f7e3532feeaeab001a30ed0c23102d6a277beac38880`.
The matching CI-built Windows ZIP delivered as `LanBridge-Windows-ec981af.zip`
is 41,943,677 bytes, SHA-256
`60e89984c3bd9ab3c58c96ced6e83e00c8f8b77c63592f63ed67947bf814052d`,
clean AMD64/Python 3.12.10/Qt 6.12.0.

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
| Updated Windows reopening | Tester quit the old build, fully extracted the verified `f530938` package and opened its EXE. After selecting a file and closing the window, opening that EXE again restored the window, retained selection and did not send, as reported by the tester. |
| Updated Windows multi-file action / reverse Decline | Tester was instructed to reinstall the native action from the new fixed location, then right-clicked the original text, Chinese/space-named text and empty file. Operator observed all three names, 78 B, in the hidden Mac's consent dialog and clicked Decline. Mac task `824a3f1f…` showed declined, 0/78 B. Exact directory inventory and existing small-file hashes remained unchanged; no staging directory remained. Tester confirmed Windows also displayed declined. |
| Windows installation status | Tester confirmed the final Windows Settings showed File-manager action: Installed and Reinstall file-manager action. |
| Mac receiver force-kill / restart cleanup | While real Windows request `a59208e3…` was receiving, operator observed payload progress, then SIGKILLed only PID 43135. An owned staging file of 90,341,376 bytes was confirmed present after termination. Finder-restarted PID 43379 automatically removed it before serving. Directory inventory, original file sizes/mtimes and original 4 GiB SHA-256 were unchanged. Windows tester reported “指定的网络名不再可用” (the specified network name is no longer available), not success. |
| Post-crash transfer recovery | Restarted Mac discovered ovitch as Online/Paired. Tester right-clicked the original 37 B text again; operator accepted its standalone prompt with main window hidden. `e021896f…` completed and saved as `(3)` with the original SHA-256; all pre-test files stayed unchanged and no staging directory remained. Tester confirmed Windows complete. |
| Editable Mac file selection | Operator chose all three original fixtures in the native picker, selected the Chinese file in the actual main-window list and clicked Remove selected. Only hello/empty remained. `e013fda5…` sent 37 B and completed on Mac; tester confirmed Windows listed only these two files and received them. All three source-file SHA-256 values remained unchanged. Actual Clear list emptied the view and disabled Send files/Clear list. Screenshots 26–27. |
| Editable Windows file selection | Tester updated to verified `597e8a3`, chose all three fixtures, Ctrl-selected Chinese/empty and removed them in the actual Windows main list. Operator observed only hello, 37 B, in Mac consent, accepted and observed `6a507a32…` complete. Received `(4)` matched the original SHA-256; pre-test files stayed unchanged and no staging remained. Tester confirmed Windows complete, Clear list empties the list/disables Send files, and all three Windows originals remain. Windows UI/filesystem statements are tester reports. |
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

![Successful real transfer after receiver force-kill and restart](images/mac-m7/25-post-crash-recovery.jpg)

## Windows Wi-Fi interruption and recovery — 2026-10-28

Both installed apps use clean `597e8a3`. Windows networking/UI/filesystem actions
below are tester reports; the Mac operator observes the native Mac UI and its
local files/processes. No firewall or TLS/pairing/consent settings were changed.
The original Mac app process is PID 51515.

- **Receiver Wi-Fi off:** Mac offered the newly named `network drop 4 GiB.bin`,
  4,294,967,296 bytes. Actual payload progress was observed beyond 74.5 MiB.
  After the tester accepted and disabled Windows Wi-Fi, Mac request `54462c84…`
  became `error: [Errno 32] Broken pipe` at approximately 2%, never complete.
  The transfer TCP connection closed while the Mac receive listeners stayed up.
  The tester reported `Receive 54462c84 error`, no new final file and no hidden
  staging remnants, then restored Wi-Fi without restarting LanBridge.
- **Same-file retry:** Mac started a new request `bfeeff85…` from 0 B without
  restarting or re-pairing. The tester accepted it. Mac observed complete at 4.0/4.0 GiB, average 20.7 MiB/s;
  the tester confirmed Windows complete and normal receipt. Windows PowerShell
  Get-FileHash returned the exact source SHA-256, and the tester separately
  confirmed no hidden staging remnants after the completed retry.
- **Local baseline:** the Mac receive-folder inventory, sizes and mtimes stayed
  unchanged through the interrupted send. No Mac staging directories appeared.
  No new application-log entries, including the earlier asyncio traceback,
  appeared during the interruption; this does not resolve the older Quit case.
- **Related isolated regression check:** six existing disconnect/cancellation/
  restart-cleanup tests passed. They use separate identities/directories and do
  not stand in for these two-computer observations.

**Reverse-role first attempt:** Windows sent the verified same file to the
hidden Mac (`76cf46fe…`). Mac accepted, and filesystem observation confirmed
83,214,336 staged payload bytes before the tester disabled Windows Wi-Fi. The
receiver timed out, removed its staging automatically and preserved the exact
pre-test files; no final network-test file appeared. Windows reported its send
error as the network name no longer available. Native Mac diagnostics had a
real defect: the task displayed empty `error:` and reset the transferred count
to zero. Screenshot 31 captures that old clean `597e8a3` behavior. Diagnostic
correction `6735dee` passed **80 tests, 1 skipped**; frozen regression follows.
The tester clarified that both prior Wi-Fi toggles were on Windows, not Mac.

![Observed empty timeout reason before the fix](images/mac-m7/31-empty-timeout-error.jpg)

**Fixed reverse-role failure/archiving:** both apps updated to clean `ec981af`.
Mac accepted `fdabb934…`, received 213,450,752 bytes (203.6 MiB), then Windows
Wi-Fi was disabled again. Mac reported Connection timed out with those bytes
preserved, displayed Failed instead of a percentage, removed all staging and
preserved its exact original files. Operator clicked Archive task: bar hidden,
Ready restored. The actual history popup retained the Archived record; operator
reselected it, reviewed the same error/bytes and archived it again. Tester
confirmed the same Failed/Archive/Ready/bar-hidden behavior on Windows. A new
request `3c8838f5…` then restored ordinary percentage progress and completed at
4.0/4.0 GiB, average 20.0 MiB/s. Its 4,294,967,296-byte Mac file matched the exact
source/Windows SHA-256. Original files stayed unchanged; no staging remained.
Tester confirmed Windows complete and successful completed-task archiving.
Mac process 52809 did not restart for these tests and was left at Ready after
archiving the final completion.

![Fixed timeout reason and Failed state with actual received bytes](images/mac-m7/32-timeout-failed-fixed.jpg)

![Archiving closes the result and returns to Ready](images/mac-m7/33-task-archived-ready.jpg)

![Archived task remains reviewable in the current session](images/mac-m7/34-archived-history-review.jpg)

![Full 4 GiB reverse retry after failure archiving](images/mac-m7/35-retry-after-archive-complete.jpg)

The large source's streaming SHA-256 was verified before the test:
`8479e43911dc45e89f934fe48d01297e16f51d17aa561d4d1c216b1ae0fcddca`.

![Real payload progress before receiver Wi-Fi interruption](images/mac-m7/28-network-outage-progress.jpg)

![Mac reports the interrupted connection as failure](images/mac-m7/29-network-outage-error.jpg)

![Same-file retry completes after Windows Wi-Fi returns](images/mac-m7/30-network-retry-complete.jpg)

## Receive storage gates — 2026-10-28–29

This phase uses the existing clean `ec981af` apps and normal Mac user profile.
Windows is the sender; Windows UI results are tester reports. Only newly created
fixture directories/volumes are restricted. The normal Desktop receive-folder
inventory is recorded and preserved; no physical disk is filled or reformatted.

### Mac receive directory loses write permission

Operator selected a writable test directory through actual Settings/Save, then
changed only that owned directory to mode 0555. Effective user is UID 501; an
independent temporary-directory write probe failed with errno 13. The directory
already contained a deliberately different `01 Mac hello.txt` sentinel.

Tester right-clicked the original 37 B hello on Windows. Operator observed the
real Mac consent dialog pointing to the test directory and clicked Accept.
Request `5f8fad5d…` became Failed with Permission denied and 0 B transferred;
Windows tester also reported Permission denied. No staging directory or new
file existed afterward. The existing same-name sentinel retained its SHA-256
`031af80dca951a33172de8c4da387e7b6aed91f53f7938a6701b7c22740322e4`
and mtime; all nine normal Desktop receive files retained their sizes/mtimes.

Actual Archive task returned Ready. Test directory permissions were restored to
0755 and App settings restored via the UI to exactly their original values,
including Desktop/LanBridge Received and login startup disabled. PID 52809 and
its listeners remained running; no re-pair/restart occurred. Existing isolated
security checks: **33 passed**. No source-code change was required for this case.
This is Mac receiving; Windows receiving/storage-denial remains a separate test.

![Real receive failure when the configured directory becomes unwritable](images/mac-m7/36-receive-permission-denied.jpg)

### Mac insufficient-space preflight

Operator created and mounted a new 64 MiB HFS+ sparse disk image, with a writable
receive directory on that separate filesystem. Measured filesystem capacity was
67,067,904 B, with 65,490,944 B free. This was an actual small-volume test, not a
mocked free-space result; the host's physical disk was not filled or reformatted.
The directory already contained a generated `existing.txt` sentinel.

Actual Settings/Save selected this directory. Tester sent `network drop 4 GiB.bin`
(4,294,967,296 B) from Windows; operator observed the correct Save to destination
in the Mac consent dialog and clicked Accept. Request `bdd18382…` became Failed /
Insufficient free space at 0 B; tester confirmed the same Windows failure.
No payload, new final file or staging directory was retained. Free space was
unchanged; the sentinel retained its mtime and SHA-256
`9a6a437ce90407f54d376d7854ca3d0ccdfc6c8d3c4995cdf54a8f246527f1ce`.
The nine original Desktop receive files retained their sizes and mtimes.
Actual Archive task returned Ready. This validates the preflight space gate,
not disk exhaustion midway through a transfer or the Windows receiver's gate.

![Real small-volume receive request fails before payload transfer](images/mac-m7/37-receive-insufficient-space.jpg)

### Restore normal settings and receive again — 2026-10-29

Operator restored Desktop/LanBridge Received through actual Settings/Save;
decoded settings matched the original snapshot, including login startup disabled.
The test directory's original 0755 permissions were restored. Only the owned
small test volume was detached; its sparse image remains in ignored test artifacts.
The recovery app process was PID 61426, different from PID 52809 on October 28:
this is recovery after restart, not a same-process continuity claim across days.

Tester resent the original 37 B hello from Windows. Operator observed the normal
Desktop destination in the real consent dialog and clicked Accept. Request
`0665cfae…` completed at 37/37 B, saved as `01 Mac hello (5).txt`, with SHA-256
`4877bb69a9a4b2443be1dab75950cbc958e36760b378c415b2c2f7b7d3430a1b`,
matching the source. All nine earlier files retained their sizes/mtimes and no
staging remained. Tester confirmed Windows complete. Actual Mac Archive task
returned Ready and hid the bar. No source-code change was required for this phase.

![Successful physical receipt after restoring the normal destination](images/mac-m7/38-storage-settings-recovery.jpg)

## Generated small-file reference hashes

| File | Bytes | SHA-256 |
| --- | --- | --- |
| `01 Mac hello.txt` | 37 | `4877bb69a9a4b2443be1dab75950cbc958e36760b378c415b2c2f7b7d3430a1b` |
| `中文 文件.txt` | 41 | `8e86973ec5151c3a279ea0ab8acb1a195e8783f6bc9884444a9fe73a1dbefdf0` |
| `empty.txt` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `large 4 GiB.bin` | 4,294,967,296 | `8479e43911dc45e89f934fe48d01297e16f51d17aa561d4d1c216b1ae0fcddca` |

## Automated checks

Latest full Mac gate after timeout/terminal-history corrections: documentation, lint/format, **83 passed, 1 Windows COM test
skipped**. Native Cocoa reopening/file-manager/desktop/history modules: **28 passed**.
The `c863854` CI completed all six jobs successfully, including both native
builds and frozen diagnostics. Inspected Python 3.12 logs: Windows **76 passed,
1 native macOS test skipped**; Mac **76 passed, 1 Windows COM test skipped**.
The startup-order follow-up `f530938` CI also completed all six jobs successfully; its Python 3.12 logs each show **76 passed, 1 platform-specific skip**.
The editable-selection `597e8a3` CI also passed all six jobs, including both
frozen builds. Inspected Python 3.12 logs on Windows and Mac each show **78 passed,
1 platform-specific skip**. Selection tests additionally validate source-file
preservation, removal of the correct same-basename path, keyboard removal and
independence from an already-started send.

The right-click tests cover explicit authenticated IPC send intent, single/multi
recipient dispatch, unpaired/offline/revoked targets, empty selections and actual
paired TLS consent without opening the sender main window. Isolated two-process accept
and decline demos and multicast smoke check passed. Actual frozen diagnostics
also passed outside the checkout and from the mounted DMG. These use temporary
identities/configuration and do not replace the physical checks above.

The `ec981af` CI run 40769388025 passed all six test/build jobs and both frozen diagnostics. Inspected Python 3.12 logs on each platform show **83 passed, 1 platform-specific skip**.

The October 29 storage-recovery full Mac gate also passed documentation,
lint/format and **83 tests, 1 Windows COM skip**. This phase changes documentation
and evidence only; the CI workflow excludes docs-only pushes.

## Remaining checks and one observed runtime log issue

- Fresh non-administrator/clean-system installation, downloaded-app quarantine
  prompts and actual logout/login have not been exercised. Login registration
  toggling was exercised; the setting was restored to disabled.
- Developer ID/notarization and Windows publisher signing remain unperformed.
  This Mac has no valid signing identity; notarytool is available.
- Three-physical-computer recipient selection, first-pairing Decline/revocation,
  Windows receiver force-kill/restart cleanup, Windows receive-storage faults,
  mid-transfer disk exhaustion and the full manual edge-case checklist are not
  yet signed off. Mac preflight low-space rejection is verified above.
- At 21:37 UTC during forced Windows receiver Quit, one non-fatal asyncio
  `_call_connection_lost` traceback was logged after the correct Connection lost
  UI error. Subsequent real transfers succeeded and cleanup was reported by the
  tester. Its signature resembles a reported [CPython duplicate-teardown issue](https://github.com/python/cpython/issues/156512),
  but this host's exact trigger has not been independently isolated; no runtime
  monkeypatch or exception suppression was applied.

During the intentional Mac SIGKILL, the Finder Quick Action that had cold-started
the app reported a Run Shell Script error, including an IMK mach-port diagnostic.
The operator dismissed it with OK before reopening the app; startup cleanup and
the subsequent real transfer passed. This observation is specific to the forced
termination and is not evidence of a normal-launch failure.

See [PROGRESS](PROGRESS.md) for checkpoint commits and CI, and
[MANUAL_ACCEPTANCE](MANUAL_ACCEPTANCE.md) for the remaining full release checklist.
