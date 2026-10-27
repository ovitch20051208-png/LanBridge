"""Build a native, unsigned development distribution with embedded Python."""

from __future__ import annotations

import argparse
import json
import os
import platform
import plistlib
import shutil
import struct
import subprocess
import sys
import tempfile
from importlib.metadata import distribution
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_environment() -> dict[str, str]:
    # Unrelated host tools can ship DLLs incompatible with Windows system ICU.
    env = dict(os.environ)
    if sys.platform == "win32":
        windows = Path(os.environ["SystemRoot"])
        paths = [Path(sys.executable).parent, Path(sys.base_prefix), windows / "System32", windows]
    else:
        paths = [
            Path(sys.executable).parent,
            Path("/usr/bin"),
            Path("/bin"),
            Path("/usr/sbin"),
            Path("/sbin"),
        ]
    env["PATH"] = os.pathsep.join(map(str, paths))
    return env


def distribution_notices(destination: Path):
    destination.mkdir(exist_ok=True)
    licenses = destination / "licenses"
    licenses.mkdir(exist_ok=True)
    for source in (ROOT / "licenses").iterdir():
        shutil.copy2(source, licenses / source.name)
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, destination / name)
    versions = {}
    for name in (
        "PySide6_Essentials",
        "shiboken6",
        "cryptography",
        "zeroconf",
        "ifaddr",
        "platformdirs",
        "cffi",
        "pycparser",
        "PyInstaller",
    ):
        package = distribution(name)
        versions[name] = package.version
        for source in package.files or []:
            if "license" in str(source).lower() or "copying" in str(source).lower():
                path = package.locate_file(source)
                if path.is_file():
                    shutil.copy2(path, licenses / f"{name}-{path.name}")
    for name in ("LICENSE.txt", "LICENSE"):
        path = Path(sys.base_prefix) / name
        if path.is_file():
            shutil.copy2(path, licenses / "Python-LICENSE.txt")
            break
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
    )
    (destination / "BUILD-INFO.json").write_text(
        json.dumps(
            {
                "version": "0.1.0",
                "commit": commit,
                "source_dirty": dirty,
                "python": platform.python_version(),
                "platform": platform.system(),
                "architecture": platform.machine(),
                "dependencies": versions,
                "signed_release": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def icon_assets(directory: Path) -> Path:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from lanbridge.ui.app import app_icon

    app = QApplication.instance() or QApplication([])
    icon = app_icon(256)
    png = directory / "icon.png"
    icon.pixmap(256, 256).save(str(png), "PNG")
    if sys.platform == "win32":
        data = png.read_bytes()
        ico = directory / "icon.ico"
        ico.write_bytes(
            struct.pack("<HHH", 0, 1, 1) + struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(data), 22) + data
        )
        return ico
    iconset = directory / "LanBridge.iconset"
    iconset.mkdir(exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        app_icon(size).pixmap(size, size).save(str(iconset / f"icon_{size}x{size}.png"), "PNG")
        app_icon(size * 2).pixmap(size * 2, size * 2).save(str(iconset / f"icon_{size}x{size}@2x.png"), "PNG")
    icns = directory / "icon.icns"
    subprocess.run(["iconutil", "-c", "icns", "-o", str(icns), str(iconset)], check=True)
    app.processEvents()
    return icns


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dmg", action="store_true", help="Also make a development DMG on macOS")
    args = parser.parse_args()
    if sys.platform not in {"win32", "darwin"}:
        parser.error("Build on Windows x86-64 or an Apple Silicon Mac")
    if sys.platform == "darwin" and platform.machine() != "arm64":
        parser.error("The macOS release target requires a native arm64 Python")
    if sys.platform == "win32" and platform.machine().lower() not in {"amd64", "x86_64"}:
        parser.error("The Windows release target requires x86-64 Python")
    directory = ROOT / "build"
    directory.mkdir(exist_ok=True)
    icon = icon_assets(directory)
    notices = directory / "notices"
    distribution_notices(notices)
    info = {
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "NSHighResolutionCapable": True,
        "LSUIElement": True,
        "NSLocalNetworkUsageDescription": "LanBridge discovers paired computers and transfers files on your local network.",
        "NSBonjourServices": ["_lanbridge._tcp"],
    }
    spec = directory / "LanBridge.spec"
    content = f"""# Generated by scripts/build.py; do not edit.
from PyInstaller.utils.hooks import collect_submodules
def keep_binary(entry):
    path = entry[0].replace('\\\\', '/')
    if '/plugins/' in path:
        relative = path.split('/plugins/', 1)[1]
        category, _, filename = relative.partition('/')
        stem = filename.split('.')[0]
        if category == 'platforms' and stem not in {{'qwindows', 'qminimal', 'qoffscreen', 'libqcocoa', 'libqminimal', 'libqoffscreen'}}:
            return False
        if category == 'imageformats' and stem not in {{'qico', 'qjpeg', 'libqico', 'libqjpeg'}}:
            return False
        if category not in {{'platforms', 'styles', 'imageformats', 'tls', 'networkinformation'}}:
            return False
    forbidden = ('Pdf', 'Qml', 'Quick', 'VirtualKeyboard', 'Svg')
    return not any(('Qt6' + name) in path or ('Qt' + name + '.framework') in path for name in forbidden)
a = Analysis([{str(ROOT / "scripts/launcher.py")!r}], pathex=[{str(ROOT)!r}],
    binaries=[], datas=[({str(notices)!r}, 'notices')], hiddenimports=collect_submodules('zeroconf', filter=lambda name: '.test' not in name) + collect_submodules('ifaddr', filter=lambda name: '.test' not in name), hookspath=[], hooksconfig={{}}, runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtQml', 'PySide6.QtQuick', 'tkinter', 'pytest'],
    noarchive=False, optimize=1)
a.binaries = [entry for entry in a.binaries if keep_binary(entry)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='LanBridge',
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    icon={str(icon)!r}, target_arch={"arm64" if sys.platform == "darwin" else None!r})
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='LanBridge')
"""
    if sys.platform == "darwin":
        content += f"app = BUNDLE(coll, name='LanBridge.app', icon={str(icon)!r}, bundle_identifier='org.lanbridge.desktop', info_plist={info!r})\n"
    spec.write_text(content, encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(ROOT / "dist"),
            "--workpath",
            str(directory / "pyinstaller"),
            str(spec),
        ],
        check=True,
        cwd=ROOT,
        env=build_environment(),
    )
    if sys.platform == "win32":
        archive = shutil.make_archive(
            str(ROOT / "dist/LanBridge-windows-x86_64-0.1.0"), "zip", ROOT / "dist", "LanBridge"
        )
    else:
        app_path = ROOT / "dist/LanBridge.app"
        # Validate metadata without mutating the already ad-hoc-signed bundle.
        plist = plistlib.loads((app_path / "Contents/Info.plist").read_bytes())
        if plist["NSBonjourServices"] != ["_lanbridge._tcp"]:
            raise RuntimeError("Local-network bundle metadata missing")
        archive = str(ROOT / "dist/LanBridge-macos-arm64-0.1.0.zip")
        subprocess.run(
            ["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app_path), archive], check=True
        )
        if args.dmg:
            with tempfile.TemporaryDirectory(prefix="lanbridge-dmg-") as temporary:
                stage = Path(temporary)
                shutil.copytree(app_path, stage / "LanBridge.app", symlinks=True)
                (stage / "Applications").symlink_to("/Applications", target_is_directory=True)
                subprocess.run(
                    [
                        "hdiutil",
                        "create",
                        "-volname",
                        "LanBridge",
                        "-srcfolder",
                        str(stage),
                        "-ov",
                        "-format",
                        "UDZO",
                        str(ROOT / "dist/LanBridge-macos-arm64-0.1.0.dmg"),
                    ],
                    check=True,
                )
    print(json.dumps({"archive": archive, "signed_release": False, "architecture": platform.machine()}))


if __name__ == "__main__":
    main()
