"""Opt-in, per-user native file-manager and login integration."""

from __future__ import annotations

import json
import os
import plistlib
import shlex
import shutil
import subprocess
import sys
import uuid
from pathlib import Path


def launch_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [sys.executable]
    executable = Path(sys.executable)
    if sys.platform == "win32" and executable.with_name("pythonw.exe").exists():
        executable = executable.with_name("pythonw.exe")
    return [str(executable), "-m", "lanbridge"]


def windows_send_to_path() -> Path:
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/SendTo/Send with LanBridge.lnk"


def install_windows(command: list[str] | None = None, *, destination: Path | None = None) -> Path:
    if sys.platform != "win32":
        raise OSError("Windows integration must be installed on Windows")
    command = command or launch_command()
    destination = destination or windows_send_to_path()
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "target": command[0],
        "arguments": subprocess.list2cmdline([*command[1:], "--send"]),
        "shortcut": str(destination),
    }
    env = {**os.environ, "LANBRIDGE_SHORTCUT": json.dumps(data)}
    script = "$d = $env:LANBRIDGE_SHORTCUT | ConvertFrom-Json; $w = New-Object -ComObject WScript.Shell; $s = $w.CreateShortcut($d.shortcut); $s.TargetPath = $d.target; $s.Arguments = $d.arguments; $s.Description = 'Send selected files with LanBridge'; $s.Save()"
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        env=env,
        check=True,
        capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return destination


def mac_workflow_path() -> Path:
    return Path.home() / "Library/Services/Send with LanBridge.workflow"


def workflow_document(command: list[str]) -> dict:
    return {
        "AMDocumentVersion": "2",
        "connectors": [],
        "actions": [
            {
                "action": {
                    "ActionBundlePath": "/System/Library/Automator/Run Shell Script.action",
                    "ActionName": "Run Shell Script",
                    "BundleIdentifier": "com.apple.RunShellScript",
                    "ActionParameters": {
                        "COMMAND_STRING": "exec " + shlex.join([*command, "--send"]) + ' "$@"',
                        "inputMethod": 1,
                        "shell": "/bin/zsh",
                    },
                    "AMAccepts": {"Container": "List", "Types": ["com.apple.cocoa.string"]},
                    "AMProvides": {"Container": "List", "Types": ["com.apple.cocoa.string"]},
                    "UUID": str(uuid.uuid4()),
                },
                "isViewVisible": True,
            }
        ],
        "workflowMetaData": {
            "serviceInputTypeIdentifier": "com.apple.Automator.fileSystemObject",
            "serviceOutputTypeIdentifier": "com.apple.Automator.nothing",
            "serviceProcessesInput": 0,
            "serviceApplicationBundleID": "com.apple.finder",
            "serviceApplicationPath": "/System/Library/CoreServices/Finder.app",
            "workflowTypeIdentifier": "com.apple.Automator.servicesMenu",
            "useAutomaticInputType": False,
        },
    }


def install_macos(command: list[str] | None = None, *, destination: Path | None = None) -> Path:
    command = command or launch_command()
    destination = destination or mac_workflow_path()
    contents = destination / "Contents"
    contents.mkdir(parents=True, exist_ok=True)
    (contents / "document.wflow").write_bytes(plistlib.dumps(workflow_document(command)))
    info = {
        "CFBundleIdentifier": "org.lanbridge.send-service",
        "CFBundleName": "Send with LanBridge",
        "NSServices": [
            {
                "NSMenuItem": {"default": "Send with LanBridge"},
                "NSMessage": "runWorkflowAsService",
                "NSSendFileTypes": ["public.item"],
            }
        ],
    }
    (contents / "Info.plist").write_bytes(plistlib.dumps(info))
    return destination


def install() -> Path:
    if sys.platform == "win32":
        return install_windows()
    if sys.platform == "darwin":
        return install_macos()
    raise OSError("Native file-manager integration supports Windows and macOS")


def uninstall():
    if sys.platform == "win32":
        windows_send_to_path().unlink(missing_ok=True)
    elif sys.platform == "darwin":
        path = mac_workflow_path()
        # This is a fixed, owned integration bundle, never a caller-provided path.
        if path.is_symlink():
            path.unlink()
        elif path.exists():
            shutil.rmtree(path)


def set_launch_at_login(enabled: bool, command: list[str] | None = None):
    command = command or launch_command()
    if sys.platform == "win32":
        import winreg

        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
        ) as key:
            if enabled:
                winreg.SetValueEx(
                    key, "LanBridge", 0, winreg.REG_SZ, subprocess.list2cmdline([*command, "--background"])
                )
            else:
                try:
                    winreg.DeleteValue(key, "LanBridge")
                except FileNotFoundError:
                    pass
    elif sys.platform == "darwin":
        path = Path.home() / "Library/LaunchAgents/org.lanbridge.desktop.plist"
        if enabled:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(
                plistlib.dumps(
                    {
                        "Label": "org.lanbridge.desktop",
                        "ProgramArguments": [*command, "--background"],
                        "RunAtLoad": True,
                    }
                )
            )
        else:
            path.unlink(missing_ok=True)
    else:
        raise OSError("Launch at login supports Windows and macOS")
