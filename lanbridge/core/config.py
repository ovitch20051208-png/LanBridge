from __future__ import annotations

import socket
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path, user_downloads_path

from lanbridge.core.storage import private_directory, read_json, write_json


def clean_device_name(name: str) -> str:
    name = name.strip()
    if not name or len(name.encode("utf-8")) > 100 or any(ord(c) < 32 for c in name):
        raise ValueError("Device name must be 1–100 UTF-8 bytes without control characters")
    return name


@dataclass
class Settings:
    directory: Path
    name: str
    downloads: Path
    launch_at_login: bool = False

    @classmethod
    def load(cls, directory: Path | None = None) -> Settings:
        directory = private_directory(directory or user_config_path("LanBridge", appauthor=False))
        data = read_json(directory / "settings.json", {})
        return cls(
            directory,
            clean_device_name(data.get("name", socket.gethostname()[:60])),
            Path(data.get("downloads", str(user_downloads_path()))).expanduser().absolute(),
            bool(data.get("launch_at_login", False)),
        )

    def save(self):
        self.name = clean_device_name(self.name)
        write_json(
            self.directory / "settings.json",
            {"name": self.name, "downloads": str(self.downloads), "launch_at_login": self.launch_at_login},
        )
