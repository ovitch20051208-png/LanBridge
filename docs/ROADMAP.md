# LanBridge milestones and next-stage gates

[中文阶段规划](ROADMAP.zh-CN.md) · [Verification record](PROGRESS.md) · [Physical evidence](M7_ACCEPTANCE.md)

Updated 2026-10-29. The owner wants current-feature testing and known functional
defects resolved before a separate UI/UX redesign branch begins. This plan
changes sequencing, not application behavior or verification results.

## Current checkpoint

- M1–M6 implementation is complete: transport, desktop, native actions,
  pairing/security, packaging and CI. The repository is now public.
- M7 physical acceptance is in progress. Both transfer directions, 4 GiB hashes,
  Finder/Windows direct send, reopening, editable file selection and failure
  archiving passed within the scopes recorded in the evidence.
- Mac receive permission-denial, preflight low-space rejection and recovery
  passed. Corresponding Windows receiver storage cases remain unverified.
- Installed app: clean `ec981af`; latest Mac full gate: 83 passed, 1 Windows COM
  skip. Its six CI jobs passed. Later docs commits do not imply newer app packages.
- Fresh installation, actual login startup, remaining edge cases and signing
  are open. No UI/UX branch or baseline tag has been created.

## Stage order and exit criteria

| Stage | Work | Exit evidence |
| --- | --- | --- |
| M7 — functional acceptance | Keep the current UI; finish physical fault, consent/trust and native-entry cases; fix functional defects on both systems. | Required cases have build/date/direction/result/cleanup evidence; known functional bugs are resolved and retested; automated checks and code-change CI pass. |
| M8 — installation and baseline | Test clean/non-admin installs, updates, uninstall, real login sessions and state preservation on both systems. Freeze V1 scope. | Retain clean-source packages, hashes, source commit, CI and acceptance record; create the baseline tag after this gate passes. |
| M9 — separate UI/UX branch | Branch from that baseline; agree shared flows/native adaptations, then implement and test one UI module at a time. | Both systems pass visual/interaction/accessibility checks and physical regression; merge after owner review. |
| M10 — release candidate | Regress the merged candidate, sign Windows/macOS builds, notarize/staple Mac, test final distributed packages and update guides. | Signed-package installation/transfer evidence, hashes, licenses and release notes; explicit release approval. |

These are evidence gates, not date estimates. A finite V1 acceptance checklist
and zero open known functional defects define readiness; no test can guarantee
that unknown bugs will never be found. Cosmetic preferences wait for M9;
misleading state, inaccessible controls, missing consent, file loss and broken
operations are fixed in M7/M8. Signing credentials belong to M10 and do not block
preparing a tested development-preview baseline.

## M7 execution rounds

| Order | Remaining work | Required observation |
| --- | --- | --- |
| 7A — Windows receiver faults | Dedicated unwritable directory, small virtual-volume preflight rejection, force-kill during payload, restart and retry. | Clear failure on both sides; preserved originals; staging cleaned at the appropriate failure/restart point; restored destination receives a hash-matching retry. |
| 7B — consent/trust | Recheck first-pairing Decline with fresh isolated identities, unanswered-request expiry, cancel while waiting/during payload from both sides, Forget during pending/active requests, re-pair and restart. | No unintended trust, payload or success; stale dialogs close; revoked trust prevents new sends; pairing/consent restore operation. |
| 7C — native/connection edges | Rapid Finder/Send To invocations, cold/warm single-instance state, duplicate basenames, changed device names, manual connection when multicast is unavailable. | Correct paths/recipient, no unrelated extra instance, preserved originals and validated output; discovery/settings restored afterward. |
| 7D — reliability | Safe mid-stream space exhaustion on owned virtual volumes, agreed longer/repeated transfers and the older nonfatal asyncio teardown traceback. | Complete/hash or explicit failure/cleanup evidence; isolate and resolve known faults before baseline sign-off. Do not suppress an unexplained traceback to declare success. |
| 7E — three physical computers | Mac A and Windows B/C: all six directed paths, multi-target routing, simultaneous tasks, peer-specific faults and trust isolation. | Pass the explicit three-computer gate below before M8 baseline sign-off; record evidence per path/task, not just discovery. |

Use [MANUAL_ACCEPTANCE.md](MANUAL_ACCEPTANCE.md) for procedures and
[M7_ACCEPTANCE.md](M7_ACCEPTANCE.md) to avoid repeating completed cases unless a
related fix changes them. The owner reports another Windows computer is available
for round 7E; its environment/build still needs verification. Missing environment
cases stay pending; a deferral needs explicit
owner acceptance and a record, never a false pass. Windows results require the
owner's observation; Mac automation cannot certify them.

Round 7A-1's Windows ACL hang is fixed on the working branch. Native regression
and two real accepted offers return prompt permission failures, with continued
service and no remnants. ACL/settings restoration and a same-process Finder retry
with an independently matching Windows hash now pass. Affected reverse/Decline/
cancel regression and main integration follow; see the [handoff](WINDOWS_DEBUG_HANDOFF.zh-CN.md).

Windows setup is guided one action at a time: restrict only a newly created
fixture directory and use an owned small VHD for space tests. Record the original
receive path and provide restoration steps. Do not fill a physical disk, change
an ordinary download folder's permissions or disable OS protections.

## M7 round 7E — three-computer gate before UI/UX

Topology: A is the current Apple Silicon Mac, B the current Windows peer, C the
additional Windows computer reported by the owner. Verify C's Windows 11 x86-64
environment, exact clean app build and reachable LAN before execution. This is
a planned test, not a completed three-computer result. Use three physical machines
with distinct identities, not three processes on one host. This topology covers
one Mac/two Windows; two Macs/one Windows remains a separate coverage extension.

1. **Discovery/pairing:** each machine lists the other two without duplicate/self
   entries. Establish each needed pair by comparing all six code groups; trust
   persists across restart. Check an online unpaired C before pairing: it must
   not become a direct-send candidate or inherit B's trust.
2. **Six directed paths:** A→B, B→A, A→C, C→A, B→C and C→B. Each is a separate
   transfer with receiver consent, complete on both sides, matching source/output
   SHA-256 and no staging residue. Use generated identifying content, including
   small, empty, Unicode and space-named files; check each receiver's own path.
3. **Target selection:** with two paired online targets, the native action shows
   the picker; choose B once, then C in a separate invocation. Only the chosen
   machine gets the request. Cancel closes selection without a send. Repeat from
   Mac and Windows; with only one eligible online target, direct request remains.
   Test equal display names with distinct identities for unambiguous routing.
4. **Overlapping tasks:** A→B and A→C; B→A and C→A; then A↔B while C→A. Confirm
   actual overlapping payload, individual consent, correct task/progress/history
   association and independent completion/hashes. Mix a large and small file to
   check responsiveness. Multi-target testing uses independent sends, not a new
   broadcast feature or permission to auto-accept.
5. **Fault isolation:** Decline/cancel one request while another runs; disconnect
   or quit B while A↔C runs; Forget B while C remains paired. Only B's affected
   requests stop; C continues. No misrouted prompt, cancellation, completion or
   cleanup; restore B and verify re-pair/retry as required.
6. **Concurrent collisions:** B/C send different generated contents with the same
   basename to A. Preserve the existing sentinel and both received contents with
   collision-safe filenames; validate hashes by content, not completion order.
7. **Lifecycle/repeat:** hide/reopen main windows and invoke both native actions
   during multi-peer operation. Keep one normal-profile app per host and stable
   identities; repeat the routing/fault cases and check all owned staging cleanup.

Record each host's OS/architecture/build/fingerprint, pairing topology, direction,
request IDs, expected recipient, source/output hashes, consent and fault results.
Mac checks and the owner's Windows reports remain distinct evidence. Local
multi-process automation supplements this gate; it cannot certify three-host LAN
behavior. Known failures are fixed/retested on both platforms before freezing.
Repeat multi-target routing and overlapping-task/fault isolation after M9 UI changes.

## M8 baseline sign-off

Before creating the tag, record:

1. Final V1 scope, completed required cases, owner-approved environmental
   deferrals and no open known functional bugs. The old teardown log issue needs
   a resolution or explicitly reviewed disposition.
2. Fresh/non-admin native installs without Python, fixed app location, action
   install/reinstall/remove, upgrades preserving identity/trust/settings, and
   uninstall preserving received files/user state.
3. Actual sign-out/sign-in with startup enabled, then disabled, on both systems;
   verify background reception and ordinary reopening. Registering a LaunchAgent
   or Run entry alone is insufficient.
4. Full checks, exact-source CI builds/frozen diagnostics and final two-way
   physical smoke using those packages. Retain binaries and SHA-256 before the
   14-day CI artifacts expire; a Git tag alone does not retain binaries.
5. Source SHA, manifests, OS/architecture, evidence and release-only prerequisites.
   Keep private identities/configuration, signing secrets and build caches out of Git.

Proposed annotated tag: `baseline/pre-uiux-v0.1.0`, a verified development-preview
baseline, not a production release or signing claim. Choose its actual commit
after M8 passes; today's app is not prematurely labeled frozen.

## M9 branch and regression contract

Create proposed branch `uiux/desktop-redesign` from the M8 tag when M9 begins.
Keep `main` at the accepted functional baseline during UI review. Commit each
validated UI module clearly and push immediately to the UI branch. First extend
CI to exercise branch native builds: currently push builds run only on `main`,
and PRs run tests without builds. Branch existence alone provides no build proof.

Agree flows/wireframes and shared design rules first. Then work through device/
file selection, incoming consent, transfer status/history, settings/receive folder
and tray/menu-bar/platform entries. Check both systems, keyboard focus, high DPI/
window sizing, long/Chinese paths and light/dark appearance. Update both guides
with real captures.

Preserve ordinary reopening without auto-send and with selection retained;
file-manager direct request to the sole paired online device or one target choice;
mandatory receive consent; reception after window close and shutdown only on Quit;
original-file preservation and SHA-256 completion; task archive/review. Automated/
development checks use isolated profiles; final native single-instance acceptance
uses the normal profile. TLS, pins and both pairing confirmations remain enabled.

After redesign, repeat two-way small/multi/empty/Unicode/collision and 4 GiB
transfers, Decline/timeout/cancel/disconnect/restart cleanup, cold/warm native entry,
hidden-window consent, settings and actual login behavior. Earlier passes do not
certify changed UI. Fix regressions before merge.

## Recovery and parallel fixes

- Retain the baseline tag and successful packages. Preserve failed experiments
  in their commits/branch; use the stable package while redesign continues.
- Functional hotfixes during M9 are fixed/tested on `main`, pushed immediately,
  then merged into the UI branch with affected checks repeated.
- Use `git revert` for published rollback; protect uncommitted work before switching.
  Never force-push or reset published history for recovery.
- This plan adds no mobile, cloud relay, auto-accept, folders or resume; new
  features need a separately agreed scope.

See [development workflow](DEVELOPMENT.md) and [security boundaries](SECURITY.md).
