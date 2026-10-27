<div align="center">

# LanBridge

**在同一局域网内，让 Windows 电脑与 Apple Silicon Mac 直接互传文件。**

[English](README.md) · **简体中文**

[完整图文操作指南](docs/USER_GUIDE.zh-CN.md) · [下载安装](#download-and-install) · [第一次传文件](#your-first-transfer) · [常见问题](docs/USER_GUIDE.zh-CN.md#troubleshooting)

</div>

发送方选择文件和接收电脑，接收方点击 **Accept（接受）**，文件就会直接传入对方设置的下载目录。
正常使用不需要浏览器、云账号，也不需要手动输入 IP。

![主界面：已配对的设备、选中的文件和 Send files 发送按钮](docs/images/user-guide/03-files-ready.jpg)

*这是实际运行的 Windows 界面，演示使用同一台电脑上的两个隔离实例，不代表完成了
Mac 与 Windows 的双机实测。当前软件界面是英文，中文文档保留按钮原名并解释含义，方便对照。*

## 先按这五步操作

1. **两台电脑都安装并运行 LanBridge**，连接到允许电脑互相访问的局域网。
   访客 Wi-Fi、设备隔离等设置可能阻止互传。
2. 在准备**接收文件的电脑**上，点击 **Allow pairing (2 min)（允许配对两分钟）**。
3. 在准备**发送文件的电脑**上，选中对方，点击 **Pair device（配对设备）**。
   核对全部六组验证码，在**两台电脑上都点击 Codes match（验证码一致）**。
4. 发送方点击 **Choose files…（选择文件）**，选中文件和接收设备，再点击 **Send files（发送文件）**。
5. 接收方在 **Incoming files（收到文件请求）** 中检查信息，点击 **Accept（接受）**。
   等状态显示 **complete（完成）**，从托盘/菜单栏的 **Received Files（已接收文件）** 打开目录。

配对通常只需做一次，但**每次传文件仍需要接收方点击 Accept**。
反方向传输时，交换两台电脑的发送方、接收方角色即可。

> **手边只有一台电脑？** 可以先查看界面，但正常互传需要另一台正在运行 LanBridge
> 的电脑。开发用的[双进程演示](docs/DEVELOPMENT.md)是单独的测试流程，不是普通用户的使用方式。

<a id="download-and-install"></a>

## 下载安装

**当前版本：0.1.0 开发预览版。** 程序包已包含 Python 运行环境，普通用户不用安装
Python，也不用执行源码开发命令。

| 你的电脑 | 使用哪个文件 | 怎么打开 |
| --- | --- | --- |
| Windows 11，x86-64 | `LanBridge-windows-x86_64-0.1.0.zip` | 完整解压，打开 `LanBridge/LanBridge.exe`。不要删掉旁边的 `_internal`，也不要只移动 exe。 |
| Apple Silicon Mac，包括 M3 | `LanBridge-macos-arm64-0.1.0.dmg` | 打开 DMG，把 `LanBridge.app` 复制到“应用程序”后再启动；也提供 arm64 应用 ZIP。 |

目前通过**公开 GitHub 仓库的 Actions 构建产物**提供程序，尚未发布签名版 Release：

1. 登录 GitHub 后，打开 [LanBridge CI](https://github.com/ovitch20051208-png/LanBridge/actions/workflows/ci.yml)。
2. 进入 `main` 分支一次成功的运行记录，找到页面下方的 **Artifacts**。
3. Windows 选择 `LanBridge-windows-2025-unsigned`；Mac 选择 `LanBridge-macos-15-unsigned`。
4. GitHub 会先下载一层“构建产物 ZIP”。解压后才能看到上表中的程序包；
   Windows 还需要继续完整解压里面的便携程序 ZIP。

Artifacts 保留 14 天；过期后，仓库所有者可以通过 **Run workflow** 重新构建。
已经拿到本地 ZIP/DMG 的话，直接使用，不需要再次下载。

程序**没有 Windows 发行者签名，也没有 macOS Developer ID 签名/公证**，系统可能提示未知应用。
请核对来源和校验值，不要关闭系统整体防护。更多内容见[安装与签名说明](docs/INSTALLATION.md)。

<a id="your-first-transfer"></a>

## 第一次传文件

### 第一步：发现设备并配对

两台都打开应用，在 **NEARBY DEVICES（附近设备）** 中点击目标电脑。
**Pairing required** 表示尚未配对，**Paired** 表示已保存对方身份。
“能够发现设备”并不等于“对方已经允许接收文件”。

接收方点击 **Allow pairing (2 min)**，发送方点击 **Pair device**。

![配对确认：六组验证码、Codes match 和 Decline 按钮](docs/images/user-guide/02-verify-pairing.jpg)

**逐组核对两边全部六组验证码**，完全一致才在两台电脑上分别点击 **Codes match**；
不一致就点击 **Decline（拒绝）**。图中验证码只是截图示例，不能重复使用。
成功配对后，重启应用仍会记住对方。

### 第二步：选择文件并发送

发送方点击 **Choose files…**，选择一个或多个文件；点击已配对的接收设备，再点击 **Send files**。
**选中文件本身不会自动发送**。系统文件选择框支持多选，当前不支持发送文件夹。

**Send files 点不了？** 请检查：是否选择了文件、是否选中了接收设备、设备是否显示 **Paired**。
列表为空时，先保持两台应用都在运行，再按[连接问题排查](docs/USER_GUIDE.zh-CN.md#troubleshooting)处理。

### 第三步：在另一台电脑上接受

![接收请求：发送方、文件名、总大小、保存位置以及 Accept 和 Decline](docs/images/user-guide/04-incoming-request.jpg)

接收方检查发送者、文件列表、总大小和 **Save to（保存到）**，然后点击 **Accept** 或 **Decline**。
不需要再选择文件，也不需要每次重新选择保存目录。主窗口关闭后，只要仍在托盘/菜单栏运行，
依然可以弹出确认窗口。
新用户默认保存到**桌面/LanBridge Received**。在 **Settings… → Save received files to → Browse… → Save** 可自选目录，也可输入新文件夹路径，Save 会创建它。已有用户保存过的路径继续使用；图中的 Windows 路径只是隔离演示目录。

接受后两边会显示进度。请等待状态变成 **complete**；100% 本身不代表最终完成。
文件自动保存，发送方收到接收方校验完成的回执后才会报告成功。

## 功能在哪里、该点哪个按钮

| 你想做什么 | 对应按钮 / 位置 | 图文说明 |
| --- | --- | --- |
| 查找并选择另一台电脑 | **NEARBY DEVICES** | [主界面](docs/USER_GUIDE.zh-CN.md#main-window) |
| 第一次配对 | 接收方 **Allow pairing (2 min)**；发送方 **Pair device** | [配对](docs/USER_GUIDE.zh-CN.md#pairing) |
| 发送单个、多文件，包含中文文件名 | **Choose files…** → 目标设备 → **Send files** | [发送文件](docs/USER_GUIDE.zh-CN.md#send-files) |
| 接受或拒绝接收 | **Incoming files** 中的 **Accept / Decline** | [接收文件](docs/USER_GUIDE.zh-CN.md#receive-files) |
| 查看速度、剩余大小和任务 | 进度区域、**Transfer history** 下拉框 | [进度和取消](docs/USER_GUIDE.zh-CN.md#progress-and-cancel) |
| 停止一项传输 | 选中相应任务 → **Cancel transfer** | [进度和取消](docs/USER_GUIDE.zh-CN.md#progress-and-cancel) |
| 找到收到的文件 | 托盘/菜单栏 → **Received Files** | [文件保存位置](docs/USER_GUIDE.zh-CN.md#saved-files) |
| 修改保存目录、设备名 | **Settings…** → 编辑 → **Save** | [设置](docs/USER_GUIDE.zh-CN.md#settings) |
| 查看、取消设备信任 | **Settings…** → **Trusted devices** → **Forget selected device** | [设备信任](docs/USER_GUIDE.zh-CN.md#settings) |
| 从资源管理器或 Finder 发送 | **Settings…** → **Install file-manager action** | [文件管理器入口](docs/USER_GUIDE.zh-CN.md#file-manager) |
| 关掉主窗口后继续接收 | 关闭窗口，通过托盘/菜单栏操作 | [后台运行](docs/USER_GUIDE.zh-CN.md#background) |
| 登录系统时自动启动 | 勾选 **Launch LanBridge in the background when I sign in**，点击 **Save** | [设置](docs/USER_GUIDE.zh-CN.md#settings) |
| 自动发现不可用时连接 | **Connect manually…** | [手动连接](docs/USER_GUIDE.zh-CN.md#manual-connection) |

传输采用加密的点对点连接、证书固定和 SHA-256 校验。同名文件会增加数字后缀，保留原文件，
不会静默覆盖。具体限制见[安全与功能边界](docs/USER_GUIDE.zh-CN.md#security-and-limits)。

## 从资源管理器或 Finder 发送

建议先用 **Choose files…** 完成一次普通传输，再在两台电脑上分别安装文件管理器入口：

1. 把程序放在以后不会随意移动的位置。
2. 打开 **Settings…**，点击 **Install file-manager action（安装文件管理器操作）**。
3. Windows：选中文件 → 右键 → **显示更多选项** → **发送到** → **Send with LanBridge**。
4. Mac：Finder 选中文件 → 右键 → **快速操作 / 服务** → **Send with LanBridge**。
5. 已经在后台运行的 LanBridge 会显示接收设备选择界面；选择目标并点击 **Send files**，
   对方仍需点击 **Accept**。

不需要管理员权限。移动程序后需要重新安装入口；移除时在设置中点击 **Remove action**。
真实 Finder/Explorer 双机流程仍待实机验收，详细步骤见[图文指南](docs/USER_GUIDE.zh-CN.md#file-manager)。

## 如果不知道该怎么继续

- **看不到附近电脑：** 确认两边都在运行、网络允许互相访问，再检查组播与设备隔离；必要时用[手动连接](docs/USER_GUIDE.zh-CN.md#manual-connection)。
- **配对失败：** 在接收方重新开放配对，再核对两边新出现的验证码。
- **对方没有接收弹窗：** 确认对方仍在托盘运行，并检查是否已配对。
- **不知道文件存到哪：** 查看 **Save to / Settings…**，从 **Received Files** 打开；同名文件可能叫 `report (1).pdf`。
- **拒绝、取消或断线：** 不应显示成功；排除原因后从头重传。

[中文图文操作指南](docs/USER_GUIDE.zh-CN.md)逐项解释了按钮位置、每一步操作与状态；
也可以切换到 [English illustrated guide](docs/USER_GUIDE.md)。

## 当前开发与验证状态

[已记录的 CI](https://github.com/ovitch20051208-png/LanBridge/actions/runs/40571919800)
通过了 Windows / Apple Silicon 测试、原生构建和打包程序自检。
Mac M3 ↔ Windows 11 双机实传、真实文件管理器操作、干净系统安装、发行签名/公证仍属于
[实机验收项目](docs/MANUAL_ACCEPTANCE.md)。

V1 不包含文件夹传输、断点续传、自动接受、手机/网页客户端、蓝牙、云中转或 Apple AirDrop 协议兼容。
**Transfer history 只记录本次运行中的近期任务，不是永久历史记录。**

## 开发者入口

以下是源码开发命令，使用打包程序不需要执行：

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -c constraints.txt -e ".[dev]"
.venv\Scripts\python scripts/check.py
.venv\Scripts\python -m lanbridge
```

macOS 使用 `.venv/bin/python`。发行包使用 Python 3.12 构建，CI 还验证 3.13。
另见[开发与 Git 回退](docs/DEVELOPMENT.md)、[架构](docs/ARCHITECTURE.md)、
[安全设计](docs/SECURITY.md)、[阶段验证记录](docs/PROGRESS.md)和[更新日志](CHANGELOG.md)。

LanBridge 自有源码采用 [MIT 许可证](LICENSE)，随程序提供的依赖保留各自的[第三方许可证](THIRD_PARTY_NOTICES.md)。
