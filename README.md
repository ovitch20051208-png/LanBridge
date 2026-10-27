# LanBridge

Local, encrypted desktop file transfer for Windows 11 and macOS Apple Silicon.
Both computers run the same application; no account, web UI, relay or cloud
storage is involved. Devices must be on a network that permits peer connections.

Development release **0.1.0**. See [progress](docs/PROGRESS.md) for tested scope
and limitations. This is not yet a signed, notarized or cross-device-certified release.

Windows and Apple Silicon CI tests, native builds and packaged-executable checks
passed in the [verified run](https://github.com/ovitch20051208-png/LanBridge/actions/runs/40571919800).
Download development packages from its Artifacts section (GitHub sign-in required).

Select a nearby computer, pair by comparing the code on both screens, then send
files. The receiver always chooses Accept or Decline. Close the main window to
continue receiving through the tray/menu bar; use Quit to stop the application.

## Development

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -c constraints.txt -e ".[dev]"
.venv\Scripts\python scripts/check.py
.venv\Scripts\python -m lanbridge
```

On macOS use `.venv/bin/python` instead. Python 3.12 or newer is required only
for source development, not for packaged distributions.

See [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md),
[installation](docs/INSTALLATION.md), [security](docs/SECURITY.md) and
[manual acceptance](docs/MANUAL_ACCEPTANCE.md). [Developer and Git workflow](docs/DEVELOPMENT.md)
documents testing, commits, rollback and CI artifacts.
