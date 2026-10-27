# Changelog

## M7 — Mac validation updates

- Prefer a usable LAN address over disconnected adapters' link-local addresses;
  display an actionable pairing timeout message.
- Remove dangling Qt framework links from Mac bundles and validate strict ad-hoc
  signature integrity before archiving.
- Make secondary buttons visibly clickable and show standalone modal prompts
  that also work while the main window is hidden.
- Default new installations to Desktop/LanBridge Received; keep saved paths and
  support creating a destination by entering its path and saving in Settings.

## Documentation update

- Added top-of-page English / Simplified Chinese navigation and equivalent user-facing READMEs.
- Added full bilingual illustrated guides covering every current control, first transfer,
  pairing, acceptance, progress, settings, native actions, background mode and manual fallback.
- Added 11 real Windows screenshots with demo provenance and documentation link / image checks.
- Clarified artifact downloads, session-only task history and remaining physical acceptance gates.

## 0.1.0 — development preview

- Local desktop send/receive with explicit Accept/Decline, background Qt receiver
  and native tray/menu-bar actions.
- Persistent identities, user-verified pairing and mutual TLS with exact pins.
- mDNS peers, manual connection fallback, SHA-256, bounded streaming, cancellation,
  replay protection, collision-safe saving and failure recovery.
- Windows Send To and generated Finder Quick Action with secure single-instance IPC.
- Native packaging scripts, Windows portable bundle, Apple Silicon build workflow,
  automated tests and reproducible two-process checks.

Development builds are unsigned/unnotarized. M7 has exercised real M3 Finder
forwarding and physical Windows/Mac transfers; the full manual checklist and
clean-machine installation remain release gates (see docs/M7_ACCEPTANCE.md).
No folder transfer, resume, auto-accept, mobile client or cloud relay is included.
