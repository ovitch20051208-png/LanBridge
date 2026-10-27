import plistlib
import subprocess
import sys
import time

import pytest
from PySide6.QtWidgets import QApplication

from lanbridge.core.storage import private_directory
from lanbridge.ipc.instance import SingleInstance, validate_request
from lanbridge.platform.integration import install_macos, install_windows, workflow_document


def test_ipc_validation(tmp_path):
    token = "a" * 64
    path = tmp_path / "你好 space.txt"
    assert validate_request({"v": 1, "token": token, "files": [str(path)]}, token) == [path]
    for request in (
        {"v": 1, "token": "wrong", "files": []},
        {"v": 1, "token": token, "files": ["relative"]},
        {"v": 1, "token": token, "files": ["bad\0"]},
        {"v": 1, "token": token, "files": [str(path)], "send": "yes"},
    ):
        with pytest.raises(ValueError):
            validate_request(request, token)


@pytest.mark.parametrize("send", [False, True])
def test_single_instance_real_local_socket(tmp_path, send):
    app = QApplication.instance() or QApplication([])
    root = private_directory(tmp_path / "state")
    received = []
    sends = []
    first = SingleInstance(root, received.append, sends.append)
    second = SingleInstance(root, lambda _: None)
    assert first.acquire()
    assert not second.acquire()
    paths = [tmp_path / "hello world.txt", tmp_path / "文件.txt"]
    try:
        code = "from PySide6.QtCore import QCoreApplication; from pathlib import Path; import sys; from lanbridge.ipc.instance import SingleInstance; app=QCoreApplication([]); peer=SingleInstance(Path(sys.argv[1]),lambda _:None); sys.exit(0 if peer.forward([Path(p) for p in sys.argv[3:]],send=sys.argv[2]=='send') else 1)"
        process = subprocess.Popen(
            [sys.executable, "-c", code, str(root), "send" if send else "open", *map(str, paths)]
        )
        deadline = time.monotonic() + 8
        while process.poll() is None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.005)
        assert process.wait(timeout=1) == 0
        assert received == ([] if send else [paths])
        assert sends == ([paths] if send else [])
    finally:
        first.close()
        app.processEvents()
    third = SingleInstance(root, lambda _: None)
    assert third.acquire()
    third.close()


def test_finder_workflow_and_quoting(tmp_path):
    command = ["/Applications/Lan Bridge's.app/Contents/MacOS/LanBridge"]
    path = install_macos(command, destination=tmp_path / "Send with LanBridge.workflow")
    document = plistlib.loads((path / "Contents/document.wflow").read_bytes())
    assert (
        document["workflowMetaData"]["serviceInputTypeIdentifier"] == "com.apple.Automator.fileSystemObject"
    )
    script = document["actions"][0]["action"]["ActionParameters"]["COMMAND_STRING"]
    assert script.endswith(' --send "$@"')
    assert script == workflow_document(command)["actions"][0]["action"]["ActionParameters"]["COMMAND_STRING"]
    assert install_macos(command, destination=path) == path
    assert sorted(p.name for p in (path / "Contents").iterdir()) == ["Info.plist", "document.wflow"]


@pytest.mark.skipif(sys.platform != "win32", reason="Real Windows COM shortcut API")
def test_windows_shortcut_native(tmp_path):
    shortcut = install_windows([sys.executable, "-m", "lanbridge"], destination=tmp_path / "LanBridge.lnk")
    assert shortcut.read_bytes()[:4] == b"L\0\0\0"
    assert shortcut.stat().st_size > 100
    assert str(shortcut).startswith(str(tmp_path))
    assert install_windows([sys.executable, "-m", "lanbridge"], destination=shortcut) == shortcut
    assert list(tmp_path.glob("*.lnk")) == [shortcut]
