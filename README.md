<div align="center">

# LanBridge

**Send files directly between a Windows PC and an Apple Silicon Mac on your local network.**

**English** · [简体中文](README.zh-CN.md)

[Illustrated user guide](docs/USER_GUIDE.md) · [Download / install](#download-and-install) · [First transfer](#your-first-transfer) · [Troubleshooting](docs/USER_GUIDE.md#troubleshooting)

</div>

Select files, choose a paired computer, and let the receiver click **Accept**.
Files travel directly between the computers and are saved to the receiver's
configured download folder. Normal transfers need no browser, cloud account or manual IP entry.

![LanBridge with a paired recipient, selected files and the Send files button](docs/images/user-guide/03-files-ready.jpg)

*Actual Windows interface. Screenshots use two local demo instances; this is not
a physical Mac-to-Windows acceptance test. The app currently uses English labels;
both documentation languages explain those same buttons.*

## Start here

1. Install **and run LanBridge on both computers** on a reachable local network.
   Guest Wi-Fi and client isolation can prevent communication.
2. On the receiving computer, click **Allow pairing (2 min)**.
3. On the sending computer, select that device and click **Pair device**.
   Compare all six code groups and click **Codes match on both computers**.
4. On the sender, click **Choose files…**, select one or more files, select the
   recipient and click **Send files**.
5. On the receiver, review **Incoming files** and click **Accept**. Wait for
   **complete**, then use tray/menu bar → **Received Files** to open the directory.

Pairing is normally done once. **Every transfer still requires Accept.**
Reverse the sender and receiver roles to send in the other direction.

> **Only one computer available?** You can inspect the interface, but a normal
> transfer needs another running LanBridge peer. The developer-only
> [two-process demo](docs/DEVELOPMENT.md) is separate from normal operation.

## Download and install

**Current version: 0.1.0 development preview.** The packages embed Python;
ordinary users do not need Python or source-development commands.

| Computer | Package | Start the app |
| --- | --- | --- |
| Windows 11, x86-64 | `LanBridge-windows-x86_64-0.1.0.zip` | Extract the whole ZIP; open `LanBridge/LanBridge.exe`. Keep `_internal` beside the executable. |
| Apple Silicon Mac, including M3 | `LanBridge-macos-arm64-0.1.0.dmg` | Open the DMG, copy `LanBridge.app` into Applications, then open the copied app. An arm64 app ZIP is also available. |

Packages are currently **GitHub Actions artifacts from the public repository**, not a signed Release:

1. Open [LanBridge CI](https://github.com/ovitch20051208-png/LanBridge/actions/workflows/ci.yml)
   while signed in to GitHub.
2. Open a successful run on `main`; scroll to **Artifacts**.
3. Download `LanBridge-windows-2025-unsigned` or `LanBridge-macos-15-unsigned`.
4. Extract GitHub's outer artifact ZIP to obtain the actual package listed above.
   For Windows, also extract the inner portable-app ZIP completely.

Artifacts are retained for 14 days. If they expire, the repository owner can use
**Run workflow** to rebuild. Already-delivered local ZIP/DMG files work directly.

Builds have **no Windows publisher signature and no macOS Developer ID signature /
notarization**. The OS may ask you to review an unknown application. Verify the
source and checksum; do not disable system-wide protections. See
[installation and signing details](docs/INSTALLATION.md).

## Your first transfer

### 1. Discover and pair

Open both apps. Under **NEARBY DEVICES**, click the intended recipient.
**Pairing required** means it has not been trusted; **Paired** means its identity
has been saved. Discovery alone does not authorize a transfer.

On the receiver, click **Allow pairing (2 min)**. On the sender, click **Pair device**.

![Pairing dialog with a six-group code, Codes match and Decline](docs/images/user-guide/02-verify-pairing.jpg)

Compare **every group** on both screens. Click **Codes match** on both only if
they match; otherwise choose **Decline**. The pictured code is an example, not a
password or reusable code. Trust persists after restart.

### 2. Choose files and send

Click **Choose files…** on the sender and select files. Select the paired
recipient and click **Send files**. Choosing files alone does not send them.
The OS file picker supports multiple selection; folders are not supported.

**Send files unavailable?** Check that files and a recipient are selected and the
device says **Paired**. For an empty list, see [connection troubleshooting](docs/USER_GUIDE.md#troubleshooting).

### 3. Accept on the receiving computer

![Incoming files: sender, names, size, destination, Accept and Decline](docs/images/user-guide/04-incoming-request.jpg)

Review the sender, file list, total size and **Save to** location. Click **Accept**
or **Decline**. The receiver does not need to choose files or a new destination
for every request. The dialog can appear while its main window is hidden.
New installations receive into **Desktop/LanBridge Received**. Use **Settings… → Save received files to → Browse… → Save** to choose another folder or enter a new folder path; Save creates it. Existing saved destinations stay in use. The pictured Windows path is an isolated demo folder.

Both computers show progress. Wait for **complete**: 100% bytes sent is not the
final result. Files are saved automatically, and the sender reports completion
only after receiving the receiver's validation receipt.

## Features and where to find them

| What you want to do | Button / location | Illustrated instructions |
| --- | --- | --- |
| Find and select a computer | **NEARBY DEVICES** | [Main window](docs/USER_GUIDE.md#main-window) |
| Pair for the first time | Receiver: **Allow pairing (2 min)**; sender: **Pair device** | [Pairing](docs/USER_GUIDE.md#pairing) |
| Send one or several files, including Unicode names | **Choose files…** → recipient → **Send files** | [Sending](docs/USER_GUIDE.md#send-files) |
| Accept or refuse incoming files | **Accept / Decline** in **Incoming files** | [Receiving](docs/USER_GUIDE.md#receive-files) |
| Inspect speed, remaining size and tasks | Progress area, **Transfer history** dropdown | [Progress and cancel](docs/USER_GUIDE.md#progress-and-cancel) |
| Stop a transfer | Select its task → **Cancel transfer** | [Progress and cancel](docs/USER_GUIDE.md#progress-and-cancel) |
| Find saved files | Tray/menu bar → **Received Files** | [Saved files](docs/USER_GUIDE.md#saved-files) |
| Change destination or device name | **Settings…** → fields → **Save** | [Settings](docs/USER_GUIDE.md#settings) |
| Inspect or forget trusted devices | **Settings…** → **Trusted devices** → **Forget selected device** | [Trust management](docs/USER_GUIDE.md#settings) |
| Send from Explorer or Finder | **Settings…** → **Install file-manager action** | [Native actions](docs/USER_GUIDE.md#file-manager) |
| Keep receiving after closing the window | Close window; use tray/menu-bar icon | [Background operation](docs/USER_GUIDE.md#background) |
| Start at sign-in | **Settings…** → **Launch LanBridge in the background when I sign in** → **Save** | [Settings](docs/USER_GUIDE.md#settings) |
| Connect when discovery is blocked | **Connect manually…** | [Manual connection](docs/USER_GUIDE.md#manual-connection) |

Transfers use encrypted peer-to-peer transport, exact certificate pins and SHA-256
validation. Existing files are preserved with numeric name suffixes. See
[security and limits](docs/USER_GUIDE.md#security-and-limits).

## Send from Explorer or Finder

First complete a transfer with **Choose files…**. Then, on each computer:

1. Keep the app in a permanent location.
2. Open **Settings…** and click **Install file-manager action**.
3. Windows: select files → right-click → **Show more options** → **Send to** → **Send with LanBridge**.
4. Mac: Finder select files → right-click → **Quick Actions / Services** → **Send with LanBridge**.
5. With exactly one paired online device, the existing instance sends the request directly. With several, click a device in the compact selector to send immediately. The receiver still clicks **Accept**; no extra **Send files** click is needed.

No administrator rights are required. Moving the app requires reinstalling the
action. Use **Remove action** to remove it. Real M3 Finder forwarding and small-file transfers to Windows passed in [M7](docs/M7_ACCEPTANCE.md); the full Explorer/Finder edge-case checklist remains a release gate.

## If something is unclear or fails

- **No nearby computer:** keep both apps running; check LAN reachability,
  multicast and client isolation. Try the [manual fallback](docs/USER_GUIDE.md#manual-connection).
- **Pairing fails:** enable pairing on the recipient and compare a new code on both screens.
- **No receive dialog:** keep the recipient running in its tray and verify pairing.
- **Missing files:** check **Save to**, Settings and **Received Files**; look for
  collision suffixes such as `report (1).pdf`.
- **Declined, cancelled or disconnected:** no success should be shown; resolve the cause and restart the transfer.

The [English illustrated guide](docs/USER_GUIDE.md) and
[中文图文操作指南](docs/USER_GUIDE.zh-CN.md) explain every control and status.

## Development status

Windows and Apple Silicon tests, native builds and frozen executable checks passed
in the [recorded CI run](https://github.com/ovitch20051208-png/LanBridge/actions/runs/40571919800).
[M7 physical testing](docs/M7_ACCEPTANCE.md) verified the M3 native app, Finder single-instance forwarding, explicit Decline and a three-file Mac → Windows → Mac round trip with matching SHA-256. The full edge-case checklist, Explorer action, clean-machine installation, actual login startup and signing/notarization remain [manual release gates](docs/MANUAL_ACCEPTANCE.md).

V1 does not include folders, interrupted-transfer resume, auto-accept, mobile/web
clients, Bluetooth, cloud relay or Apple's AirDrop protocol. **Transfer history
is a current-session UI, not a permanent audit log.**

## For developers

These commands are for source development; packaged-app users do not need them:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -c constraints.txt -e ".[dev]"
.venv\Scripts\python scripts/check.py
.venv\Scripts\python -m lanbridge
```

On macOS use `.venv/bin/python`. Builds use Python 3.12; CI also checks 3.13.
See [development / Git rollback](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md),
[security](docs/SECURITY.md), [milestone evidence](docs/PROGRESS.md) and [change log](CHANGELOG.md).

LanBridge source: [MIT](LICENSE). Dependencies retain their own [licenses](THIRD_PARTY_NOTICES.md).
