# Development and recoverable milestones

Use Python 3.12 for the distributable builds. CI also tests Python 3.13. Create a
virtual environment, then install `python -m pip install -c constraints.txt -e '.[dev]'`.
Only PySide6 Essentials is needed: Widgets, Core, Gui and Network; the full Qt
WebEngine/PDF add-ons are not application dependencies.

Run the full fail-fast gate before committing:

```
python scripts/check.py
python scripts/two_peer_demo.py
python scripts/two_peer_demo.py --decline
python scripts/smoke_discovery.py
```

The first command includes the two-process tests; the explicit demos are useful
interactive diagnostics. Live multicast smoke is separate because hosted runners
and some networks block multicast. All transfer integration tests use real
loopback sockets, separate identities and receiver decisions.

The gate also runs `scripts/check_docs.py`: local README/guide links, translated
navigation, section anchors and referenced image assets must resolve. When updating
the English UI guide, update its Chinese counterpart and retain matching button
names. Screenshot provenance is recorded in `docs/images/user-guide/README.md`.

For two visible desktop instances:

```
python -m lanbridge --data-dir <absolute-state-A> --port 0
python -m lanbridge --data-dir <absolute-state-B> --port 0
```

Never use a real user's state directory in automated tests. State includes keys
and pins and must not be committed. The `work/` folder in the enclosing Codex
workspace holds the development environments; the Git repository is self-contained.

## Git workflow

Each completed milestone has a separate tested commit. Use `git log --oneline`
and `git show <sha>` to locate changes; `git bisect` with a reproducible failing
test can isolate regressions. Shared rollback should use `git revert <sha>` and
then rerun tests, preserving history. Never force-push or reset published history
as a normal recovery mechanism. Uncommitted work must be reviewed before checkout.

The remote is the owner's private `LanBridge` repository. After checks pass:

```
git add <reviewed-files>
git commit -m '<meaningful change>'
git push origin main
```

## CI and build provenance

`.github/workflows/ci.yml` tests Windows x86-64 and macOS 15 arm64 on Python
3.12/3.13. After tests pass, native runners build their own distributions,
execute the frozen diagnostic and upload ZIP/DMG artifacts. Actions are pinned
to verified upstream commit SHAs; workflow permissions are read-only. There is
no publishing workflow and no signing secret requirement.

Inspect the Actions run for the exact source commit before claiming CI success.
Artifacts expire after 14 days. Documentation-only pushes intentionally skip
builds; the verification record identifies the last code/build commit tested.
macOS runner tests do not certify real Finder interaction or physical Mac ↔
Windows transfers. Follow MANUAL_ACCEPTANCE.md before a production release.
