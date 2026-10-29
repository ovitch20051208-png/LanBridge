# M7 / 7A Windows 接收权限卡住：本机诊断交接

更新于 2026-10-29。当前是**已发现、尚未修复的功能 Bug**，不进入 UI/UX 改版。
项目：`https://github.com/ovitch20051208-png/LanBridge`。
先读 [阶段规划](ROADMAP.zh-CN.md)、[实机证据](M7_ACCEPTANCE.md)、
[安全设计](SECURITY.md)、[开发流程](DEVELOPMENT.md)及本机适用的 AGENTS.md。

## 分工和代码状态

Windows 侧负责此项原生诊断/修复，Mac 侧保留发送现场并做后续跨平台回归。
交接时 Mac 没有修改传输源码。仓库已公开；同步最新 main，保护已有未提交改动。
二进制目录不是源码仓库；如没有源码，克隆到新的 `LanBridge-source` 目录。
确认根因后在 `fix/windows-staging-denied` 分支修复，每个独立模块检查后立即 commit
并推送分支；Mac 复核/回归后再合入 main，不 force-push，不重写历史。

不要重新实现已完成的传输、配对、原生入口等功能；不开始其他阶段。

## 已确认的现场

| 项目 | 证据 |
| --- | --- |
| Windows 包 | 所有者提供包内 BUILD-INFO：`ec981af75eb03f5e1df06c8afb51c8d23e640151`、`source_dirty=false`、0.1.0、AMD64、Python 3.12.10、Qt 6.12.0。 |
| Windows EXE | `C:\Users\ovitc\Desktop\LanBridge_V5\LanBridge\LanBridge.exe`。诊断前监听 PID 6940；之后所有者已从托盘 Quit 并重开，**不能继续假定 PID 还是 6940**。 |
| Windows 地址 | WLAN `10.137.199.4`，网关 `10.137.199.1`；另有若干 APIPA 网卡。Mac 是 `10.137.199.3`，测试时在同网段。地址需重新核对，不写死进产品。 |
| 测试接收目录 | `C:\Users\ovitc\Desktop\LanBridge Permission Test`，已在真实 App Settings 选中并 Save。 |
| 权限备份 | `C:\Users\ovitc\Desktop\LanBridge Permission Test.acl`，位于目录外，须保留用于恢复，不是新下载的软件。 |
| 限制方式 | 对新建空目录执行 `icacls /save` 后，以交互用户 SID `/deny *SID:(WD,AD)`；无递归/继承标记，不修改正常接收目录或桌面父目录。两条命令均报告 1 个成功、0 个失败。 |
| 实际写入探针 | `New-Item -ItemType Directory ...\write-probe` 报 UnauthorizedAccessException / CreateDirectoryUnauthorizedAccessError，证实创建子目录被拒绝。 |
| UI | 所有者报告主窗口及 Settings 仍可点击；端口所属 LanBridge 的 Responding=True。**这不能证明网络线程正常。** |
| 文件清理 | 最后一次 Accept 后，所有者执行 `Get-ChildItem -Force`，测试目录没有任何条目输出。 |

真实 Mac 发送的是生成的 `01 Mac hello.txt`，37 B，源 SHA-256：
`4877bb69a9a4b2443be1dab75950cbc958e36760b378c415b2c2f7b7d3430a1b`。
Mac 使用 `/Applications/LanBridge.app` 的干净 arm64 `ec981af` 正常用户配置，
PID 61426，接收目录仍为桌面/LanBridge Received；十个已有文件未变、无 Mac 暂存。

## 实际尝试及范围

- `5dfc0670…`：Mac 等待接受；所有者未确认接受。操作员从 Mac 取消并归档，0/37 B。
  此次不能用来判定 Windows 权限处理通过。
- `f78fcf23…`、`81b3150d…`：Mac 报 TLS handshake 超过 10 秒；Windows 无请求。
  Mac lsof 在后者看到 `10.137.199.3 → 10.137.199.4:47384 ESTABLISHED`；
  Windows 命令确认该端口属于 LanBridge，不是地址/端口未知。
- 当时独立 mDNS 查询无 Windows 回答，Mac 旧条目仍标 Online；暂不把这一现象
  单独定为发现功能的根因。Windows 日志尾部只有 10 月 27–28 日的三条旧错误。
- 所有者 Quit/重开同一包后，Mac 再次收到相同 Windows 身份的设备广播。
- `4a7fd4cc…`：重开后 TLS 成功，Mac 进入等待接受；所有者确认 Incoming files
  出现并点击 Accept，但 Windows 主窗口不变化，没有权限错误，目录仍为空。
  最后 Mac 报 Connection timed out，0/37 B。**重开没有修复此 Bug。**
- Mac 已归档失败并回到 Ready；Windows 最终是否已退出/是否仍在重试须先检查。

![Mac：后续请求 TLS 握手超时](images/mac-m7/39-windows-receiver-tls-stall.jpg)

![Mac：Windows 点击 Accept 后，发送端最终超时](images/mac-m7/40-windows-acl-accept-timeout.jpg)

## 明确候选：暂存目录创建重试阻塞网络循环

`lanbridge/network/transfer.py` 在接收方 Accept 后同步调用
`tempfile.mkdtemp(..., dir=directory)`。CPython 3.12 的实现对 PermissionError 有
Windows 特例：当 `isdir(dir)` 且 `os.access(dir, W_OK)` 为真时，继续尝试新名字，
直到 TMP_MAX。查看[上游源码](https://github.com/python/cpython/blob/3.12/Lib/tempfile.py)。
若 NTFS ACL 拒绝创建，但 os.access 仍为真，大量同步重试会阻塞 asyncio 网络线程，
使 UI 仍响应而收件不回执、后续握手/发现停滞。

Mac 上的隔离行为模型复现了连续四次 PermissionError 后继续重试；模型主动终止，
没有修改文件系统。**这不是原生 NTFS 复现或实际线程栈，根因仍须 Windows 验证。**

## Windows 侧执行顺序

1. 先只读采证：源码状态、系统/架构、包版本、当前 PID/监听者、日志、接收路径、
   目录 ACL、交互用户和诊断命令的 SID。不要输出私钥、IPC token 或完整用户配置。
   若有可用的安全线程/调用栈工具，优先确认卡住位置；不要盲目安装调试驱动。
2. 使用**原生 Windows x64 Python 3.12**和隔离配置/目录建立有时限的复现。
   记录直接 mkdir 的权限错误、`os.access(W_OK)` 和 tempfile 行为；旧 tempfile 测试
   放进可限时终止的专用子进程，避免卡住 Codex/pytest/用户应用。不以 WSL 结果代替 NTFS。
3. Codex 沙盒可能使用不同用户/权限。记录真实运行身份；交互用户的拒绝 ACL
   不一定限制另一个沙盒 SID。自动化应在自己新建目录拒绝实际测试 SID，结束后恢复；
   真实 App 复测仍由当前用户运行。需要额外目录访问时按现有权限流程申请，不关闭沙盒/
   防火墙，不借用管理员绕过 ACL 后宣称通过。
4. 确认后做最小修复：创建暂存目录时权限/磁盘错误及时返回；只对真实命名冲突有限重试。
   可采用不可预测随机名的原子 mkdir，保留私有模式、现有 owner marker/前缀及清理规则。
   不用 os.access 替代真实 ACL 检查，不吞异常，不通过扩充权限让测试通过。
5. 回归必须验证：NTFS 拒绝时双方迅速 Failed/非空原因、0 内容、无暂存，网络服务继续
   能处理后续请求；命名碰撞不覆盖已有目录/文件；正常成功、Decline、取消、重启清理仍通过。
6. 运行相关检查及 `python scripts/check.py`；修复 commit/推送分支后报告准确 SHA、CI、
   原生包自检和实机结果，安排 Mac 回归及真实双机接受后的权限拒绝测试，再合入 main。
   全量已有测试通过不能替代这次失败场景。

## 恢复现场

先完成必要采证。需要结束挂住应用时只操作这一个 LanBridge 测试进程，记录退出方式；
不要结束其他进程。权限备份可恢复唯一测试目录：

```powershell
icacls.exe 'C:\Users\ovitc\Desktop' /restore 'C:\Users\ovitc\Desktop\LanBridge Permission Test.acl'
```

确认输出仅恢复测试目录、写入探针恢复成功，再在真实 App Settings 选回原来的桌面
`LanBridge Received`，Save。检查有无迟到的暂存并按应用正常清理路径处理。
保留 `.acl` 到恢复确认；不自动删除用户文件。只有恢复后真实重传、落盘哈希和双方
complete 均确认，才能签字完成 7A-1；7A 空间/强制结束、7B–7E 仍是后续工作。
