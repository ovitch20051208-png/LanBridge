import ctypes
import sys

import pytest

from lanbridge.platform import macos_events


@pytest.mark.skipif(sys.platform != "darwin", reason="Native macOS AppleEvent manager")
def test_native_reopen_callback_and_cleanup(qapp):
    calls = []
    handler = macos_events.MacReopenHandler(lambda: calls.append("reopen"))
    try:
        macos_events._message(
            handler.target,
            "handleReopen:withReply:",
            None,
            (ctypes.c_void_p, ctypes.c_void_p),
            (None, None),
        )
        assert calls == ["reopen"]
        assert macos_events.REOPEN_APPLICATION == int.from_bytes(b"rapp", "big")
    finally:
        target = handler.target
        handler.close()
        handler.close()
    assert target not in macos_events._callbacks
