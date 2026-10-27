# User-guide screenshot provenance

Captured on Windows 11 on 2026-10-27 from LanBridge 0.1.0 source at `f82ea2b`,
using Qt 6.12.0 and the Computer Use window capture API. JPEG files are actual
window captures, without generated UI elements or rewritten labels.

Two isolated local Windows instances used separate identities and state. Their
loopback pairing used signed transcripts and matching real session codes. The
accepted transfer sent three fixture files, including a 64 MiB file and a Unicode
filename; all received SHA-256 digests matched. Artificial pacing kept progress
visible for capture; it did not simulate success.

The nearby rows refer to real local endpoints, not an observed remote Mac. The
Settings address is loopback and folders are isolated fixtures. The manually
typed `192.168.1.20:55187` is a format example; the dialog was cancelled without
connecting. The tray image is the production menu opened by a fixture helper.

No private keys, IPC tokens, user documents or host LAN addresses are included.
Public demo fingerprints and one-time codes are illustrative. macOS UI, actual
Explorer/Finder actions and physical cross-platform acceptance are not claimed.

| Image | Interface / state |
| --- | --- |
| 01-nearby-devices.jpg | Selected real local peer before pairing |
| 02-verify-pairing.jpg | Actual pairing code and decision buttons |
| 03-files-ready.jpg | Paired peer and files supplied through real single-instance IPC |
| 04-incoming-request.jpg | Receiver request before file content is accepted |
| 05-transfer-progress.jpg | Active paced transfer and cancel control |
| 06-transfer-complete.jpg | Sender completion after receiver validation |
| 07-settings.jpg | Actual settings and isolated fixture values |
| 08-manual-mode.jpg | Manual pairing mode selector |
| 09-manual-address.jpg | Address-format example, not submitted |
| 11-tray-menu.jpg | Production tray menu |
| 12-transfer-declined.jpg | Declined request with no bytes sent |

Both documentation languages use these same images and exact English UI labels.
