# Troubleshooting

**No nearby devices:** verify both apps are running, the same reachable LAN is
used and Wi-Fi guest/client isolation is off. VPNs and multicast filtering can
hide mDNS. LanBridge uses UDP 5353 for discovery, TCP 47384 by default for TLS,
and the pairing port displayed in Settings. Pairing ports may change at restart.
Use Connect manually as a fallback. A network that blocks peer-to-peer traffic
cannot be fixed by the app; no cloud relay is provided.

**Pairing unavailable:** click Allow pairing on the recipient, then initiate
from the sender. Compare every group on both screens. Never approve a mismatch.
If pairing was interrupted, repeat it. Forget the old identity after a device
reinstall or state reset; copying only a certificate does not restore its key.

**Transfer refused:** both sides must trust each other's current certificates.
Check device clocks and the 90-second consent deadline. Unpairing on one side
requires pairing again. Check free disk space and destination permissions.

**Transfer interrupted:** retry from the beginning. Partial staging is removed
on normal cancellation or next startup. If the final receipt was lost, inspect
the destination before retrying; complete files may already be present. Existing
files are preserved with numeric collision suffixes.

**Filename rejected:** V1 rejects paths, Windows reserved names, trailing
spaces/dots, control characters, alternate data streams and names over 240 UTF-8
bytes. Rename the source to a portable name. Folder transfer is not supported.

**Send To / Quick Action disappeared:** reinstall the action from Settings.
Reinstall after moving the app or removing its development virtual environment.
On Mac, enable the service in keyboard-shortcut / Services settings if hidden.

**A second invocation times out:** quit the existing process from its tray first.
If it has crashed, restart; the lock and stale endpoint recover automatically.
Do not delete state while a live transfer is running. Test instances need
different `--data-dir` locations and different ports (or `--port 0`).

**App fails to launch:** run its isolated self-test and review the JSON report.
Normal frozen startup errors save `startup-error.log` under the per-user
LanBridge log directory. For source development use `--verbose` from a terminal.
Never include private-key.pem, ipc.json or private file contents in bug reports.

**Native build loads the wrong DLL:** build.py sanitizes the build subprocess
PATH to avoid unrelated native tools supplying incompatible ICU/OpenSSL DLLs.
Always rerun the frozen-bundle smoke test after changing packaging dependencies.
