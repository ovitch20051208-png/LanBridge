# Milestones

Each milestone is tested before its commit. Additional fixes get separate commits.
Do not rewrite published history; use `git revert <commit>` for shared rollback.

1. **P2P core**: isolated identities, real mutually authenticated TLS sockets,
   consent, streamed multi-file transfer, safe storage and useful failures.
2. **Desktop**: PySide6 nearby devices, mDNS, incoming dialogs, background loop,
   progress and tray lifecycle.
3. **Native integration**: authenticated single-instance IPC, Windows Send To,
   Finder Quick Action, Unicode file paths and optional login startup.
4. **Security/reliability**: verified pairing, trust management, strict metadata,
   replay protection, cancellation, hostile-input and interruption tests.
5. **Packaging**: native PyInstaller builds, portable Windows bundle, Apple
   Silicon app/DMG scripts, install/uninstall and unsigned-build documentation.
6. **GitHub/CI**: private repository, Windows/macOS tests/builds/artifacts,
   reproducible manual acceptance and release notes.

Release gate: a real Finder → Windows Accept → Downloads transfer and the reverse,
including decline/cancel/offline cases. Automated tests and CI do not replace this gate.
See `docs/PROGRESS.md` for actual evidence and outstanding verification.
