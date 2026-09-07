"""Bounded background reads with latest-request-wins delivery on the UI thread."""
from __future__ import annotations

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal, Slot

log = logging.getLogger(__name__)


class _Signals(QObject):
    completed = Signal(int, object, object)


class _Read(QRunnable):
    def __init__(self, version: int, read: Callable):
        super().__init__()
        self.version, self.read = version, read
        self.signals = _Signals()

    def run(self):
        try:
            result = self.read()
        except Exception as error:
            log.exception("Background UI read failed")
            self.signals.completed.emit(self.version, None, error)
        else:
            self.signals.completed.emit(self.version, result, None)


class AsyncLoader(QObject):
    """At most one running read + one replaceable pending read per instance.

    Callables must open their own sessions and return detached data, never Qt
    widgets or ORM objects. Failed reads emit a caller-provided safe message.
    """
    loaded = Signal(object)
    failed = Signal(str)
    busy_changed = Signal(bool)

    def __init__(self, parent=None, *, error_message="Unable to load data. Please try again."):
        super().__init__(parent)
        self._version = 0
        self._active = None
        self._pending = None
        self._error_message = error_message

    def load(self, read: Callable) -> None:
        self._version += 1
        self._pending = (self._version, read)
        if self._active is None:
            self.busy_changed.emit(True)
            self._start_pending()

    def _start_pending(self):
        version, read = self._pending
        self._pending = None
        self._active = _Read(version, read)
        self._active.signals.completed.connect(self._complete, Qt.ConnectionType.QueuedConnection)
        QThreadPool.globalInstance().start(self._active)

    @Slot(int, object, object)
    def _complete(self, version, result, error):
        self._active = None
        if self._pending is not None:
            self._start_pending()
            return
        self.busy_changed.emit(False)
        if version == self._version:
            if error is None:
                self.loaded.emit(result)
            else:
                self.failed.emit(self._error_message)
