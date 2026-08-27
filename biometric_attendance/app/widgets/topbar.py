"""TopBar widget — page title, current time, logged-in user."""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from biometric_attendance.app.styles import theme
from biometric_attendance.core.dtos.auth_dtos import SessionUser

import datetime


class TopBar(QFrame):
    """Horizontal bar at the top of the content area.

    Shows the page heading on the left, user name + live clock on the right.
    """

    def __init__(self, user: SessionUser, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._user = user
        self.setObjectName("TopBar")
        self.setFixedHeight(theme.TOPBAR_HEIGHT)
        self._build_ui()
        self._start_clock()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(8)

        # Left: page title (updated by AppShell on navigation)
        self._title_label = QLabel("Dashboard")
        self._title_label.setObjectName("TopBarTitle")
        layout.addWidget(self._title_label)

        layout.addStretch()

        # Right: time and user
        right = QWidget()
        right.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        self._time_label = QLabel()
        self._time_label.setObjectName("TopBarTimeLabel")
        right_layout.addWidget(self._time_label)

        separator = QLabel("|")
        separator.setObjectName("TopBarTimeLabel")
        right_layout.addWidget(separator)

        user_label = QLabel(f"👤  {self._user.display_name}")
        user_label.setObjectName("TopBarUserLabel")
        right_layout.addWidget(user_label)

        layout.addWidget(right)

    def _start_clock(self) -> None:
        self._tick()
        timer = QTimer(self)
        timer.setInterval(1000)
        timer.timeout.connect(self._tick)
        timer.start()

    def _tick(self) -> None:
        now = datetime.datetime.now()
        self._time_label.setText(now.strftime("%A, %B %d, %Y  %I:%M:%S %p"))

    def set_page_title(self, title: str) -> None:
        """Called by AppShell when the user navigates to a different page."""
        self._title_label.setText(title)
