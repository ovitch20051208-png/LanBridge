# Installation and file-manager integration

## Source development

Use Python 3.12+ and a virtual environment, then `python -m pip install -e ".[dev]"`.
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
