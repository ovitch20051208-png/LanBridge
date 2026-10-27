import os

import pytest

from lanbridge.core.identity import Identity, TrustStore

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    return app


@pytest.fixture
def peers(tmp_path):
    a = Identity(tmp_path / "a")
    b = Identity(tmp_path / "b")
    at = TrustStore(a.directory / "trust.json")
    bt = TrustStore(b.directory / "trust.json")
    # Test provisioning only. Desktop pairing requires approval on both devices.
    at.add(b.pem, "Receiver")
    bt.add(a.pem, "Sender")
    return a, at, b, bt
