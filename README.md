# LanBridge

Local, encrypted desktop file transfer for Windows 11 and macOS Apple Silicon.
Both computers run the same application; no account, web UI, relay or cloud
storage is involved. Devices must be on a network that permits peer connections.

Development release **0.1.0**. See [progress](docs/PROGRESS.md) for tested scope
and limitations. This is not yet a signed, notarized or cross-device-certified release.

## Development

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m lanbridge
```

On macOS use `.venv/bin/python` instead. Python 3.12 or newer is required only
for source development, not for packaged distributions.

See [architecture](docs/ARCHITECTURE.md), [roadmap](docs/ROADMAP.md),
[installation](docs/INSTALLATION.md), [security](docs/SECURITY.md) and
[manual acceptance](docs/MANUAL_ACCEPTANCE.md).
