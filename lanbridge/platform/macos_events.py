"""Handle the explicit macOS reopen AppleEvent without changing background activation."""

from __future__ import annotations

import ctypes
import logging
import sys
from collections.abc import Callable

log = logging.getLogger(__name__)
POINTER = ctypes.c_void_p
CORE_EVENT = int.from_bytes(b"aevt", "big")
REOPEN_APPLICATION = int.from_bytes(b"rapp", "big")
_callbacks: dict[int, Callable[[], None]] = {}
_objc = None
_handler_class = None


@ctypes.CFUNCTYPE(None, POINTER, POINTER, POINTER, POINTER)
def _reopened(receiver, _selector, _event, _reply):
    callback = _callbacks.get(receiver)
    if callback:
        try:
            callback()
        except Exception:
            log.exception("Could not reopen the LanBridge window")


def _runtime():
    global _objc, _handler_class
    if _objc is None:
        ctypes.CDLL("/System/Library/Frameworks/Foundation.framework/Foundation")
        _objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
        for name, result, arguments in (
            ("objc_getClass", POINTER, [ctypes.c_char_p]),
            ("sel_registerName", POINTER, [ctypes.c_char_p]),
            ("objc_allocateClassPair", POINTER, [POINTER, ctypes.c_char_p, ctypes.c_size_t]),
            ("class_addMethod", ctypes.c_bool, [POINTER, POINTER, POINTER, ctypes.c_char_p]),
            ("objc_registerClassPair", None, [POINTER]),
        ):
            function = getattr(_objc, name)
            function.restype, function.argtypes = result, arguments
        base = _objc.objc_getClass(b"NSObject")
        _handler_class = _objc.objc_allocateClassPair(base, b"LanBridgeReopenEventHandler", 0)
        if not _handler_class or not _objc.class_addMethod(
            _handler_class,
            _objc.sel_registerName(b"handleReopen:withReply:"),
            ctypes.cast(_reopened, POINTER),
            b"v@:@@",
        ):
            raise OSError("Could not register the macOS application reopen handler")
        _objc.objc_registerClassPair(_handler_class)
    return _objc


def _message(receiver, selector, result=POINTER, argument_types=(), arguments=()):
    objc = _runtime()
    # A separate typed callable for each signature avoids mutating objc_msgSend's ABI.
    function = ctypes.CFUNCTYPE(result, POINTER, POINTER, *argument_types)(
        ctypes.cast(objc.objc_msgSend, POINTER).value
    )
    return function(receiver, objc.sel_registerName(selector.encode("ascii")), *arguments)


class MacReopenHandler:
    def __init__(self, reopen: Callable[[], None]):
        if sys.platform != "darwin":
            raise OSError("Application reopen events are a macOS integration")
        self.target = None
        objc = _runtime()
        self.manager = _message(objc.objc_getClass(b"NSAppleEventManager"), "sharedAppleEventManager")
        target = _message(_message(_handler_class, "alloc"), "init")
        if not self.manager or not target:
            raise OSError("Could not initialize the macOS application reopen handler")
        self.target = target
        _callbacks[target] = reopen
        _message(
            self.manager,
            "setEventHandler:andSelector:forEventClass:andEventID:",
            None,
            (POINTER, POINTER, ctypes.c_uint32, ctypes.c_uint32),
            (target, objc.sel_registerName(b"handleReopen:withReply:"), CORE_EVENT, REOPEN_APPLICATION),
        )

    def close(self):
        if self.target:
            _message(
                self.manager,
                "removeEventHandlerForEventClass:andEventID:",
                None,
                (ctypes.c_uint32, ctypes.c_uint32),
                (CORE_EVENT, REOPEN_APPLICATION),
            )
            _callbacks.pop(self.target, None)
            _message(self.target, "release", None)
            self.target = None
