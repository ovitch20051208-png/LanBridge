# Installation and file-manager integration

## Source development

Use Python 3.12+ and a virtual environment, then `python -m pip install -e ".[dev]"`.
For the verified dependency set add `-c constraints.txt` to the install command.
Start with `python -m lanbridge`. Use `--data-dir <absolute-directory> --port 0`
for an isolated second test instance. Logs go to the launching console;
`--verbose` enables diagnostic logging.

## Native actions (explicit opt-in)

In Settings choose **Install file-manager action**, or run:

```
python -m lanbridge --install-integration
python -m lanbridge --uninstall-integration
```

Windows: the installer writes only the current user's **Send To** shortcut.
Select files in Explorer → right-click → Show more options → Send to →
Send with LanBridge. It supports OS-supplied multiple paths, spaces and Unicode.
The Windows command-line length limit still applies; use the application file
picker for selections with exceptionally long aggregate paths.

macOS: a Finder Automator Quick Action is installed at
`~/Library/Services/Send with LanBridge.workflow`. Select files → right-click →
Quick Actions / Services → Send with LanBridge. If hidden, enable it in System
Settings → Keyboard → Keyboard Shortcuts → Services (location varies by macOS).
The action invokes the app executable directly, forwarding arguments through
secure single-instance IPC even when the menu-bar application is already running.
Keep the app at the path used when installing; reinstall the action after moving it.
Source installations retain the virtual environment's Python path.

Uninstalling the action leaves user files, settings and received downloads intact.
Launch at login is off by default; enable/disable it in Settings. Windows uses
the current-user Run registry key; macOS writes a per-user LaunchAgent effective
at the next login. No administrator rights or firewall changes are requested.

Native Finder execution and real Mac/Windows file-manager acceptance remain
manual release gates. The Windows test creates a real shortcut in a temporary
directory; it does not install an action in the developer's personal Send To folder.

## Windows portable distribution

Extract the complete `LanBridge-windows-x86_64-0.1.0.zip` archive to a permanent
folder. Run `LanBridge/LanBridge.exe`. Keep the `_internal` folder beside the
executable. Python is embedded; users do not need a Python installation.
To install for the current user and optionally add Send To:

```powershell
powershell -NoProfile -File scripts/install_windows.ps1 -Archive <zip-path> -InstallSendTo
```

This places the app under `%LOCALAPPDATA%\Programs\LanBridge` and creates a Start
menu shortcut. It does not change the firewall, request elevation or enable
login startup. Quit the old instance before updating. Remove with
`powershell -NoProfile -File scripts/uninstall_windows.ps1`; received files and
application state are preserved. These user-level install scripts are provided
with the source; the portable bundle is also directly usable.

## macOS development distribution

On a native arm64 Python environment:

```
python3 -m pip install -c constraints.txt -e '.[dev]'
sh scripts/build_macos.sh
```

The build produces `dist/LanBridge.app`, an arm64 ZIP and a development DMG.
Copy the app into Applications before installing the Finder action. Accept the
macOS Local Network permission prompt if shown. The bundle declares its Bonjour
service and local-network usage.

## Building and diagnostics

Windows: `python scripts/build.py`, then
`python scripts/smoke_bundle.py dist/LanBridge/LanBridge.exe`.
Mac: the shell script above builds and runs the same diagnostic on the bundle.
The diagnostic launches the actual frozen executable outside the checkout,
loads its Qt platform plugin, accepts a test dialog, transfers a Unicode file
over mutual TLS and checks the bytes. It creates only temporary loopback state.

`LanBridge --self-test-report <absolute-json-path>` writes a diagnostic report
without a normal desktop session. `notices/BUILD-INFO.json` inside the bundle's
resources records the source commit, dirty state, Python, dependency versions
and architecture. Startup errors in normal packaged mode are written to the
OS's per-user LanBridge log directory and shown in an actionable error dialog.

## Signing status

Development builds are **not signed with a Windows publisher certificate** and
**not Developer ID signed or notarized**. Windows SmartScreen and macOS
Gatekeeper may warn or block. Verify the source and archive hash before making
an explicit OS exception; do not disable system-wide protections.

PyInstaller may apply an ad-hoc Mac signature for Apple Silicon execution; this
does not identify a publisher or constitute notarization. Public distribution
needs Windows Authenticode signing or macOS Developer ID hardened-runtime
signing, notarization (`notarytool`) and stapling, using owner-controlled
credentials. No signing credentials are included or configured here. Dependency
license and source-access obligations are described in THIRD_PARTY_NOTICES.md.
