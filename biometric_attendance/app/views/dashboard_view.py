"""Dashboard placeholder view (Phase 1).

A minimal dashboard that shows the greeting, date/time, user name,
and KPI card placeholders. Real data will be wired in Phase 3+.
"""
from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.styles import theme
from biometric_attendance.core.dtos.auth_dtos import SessionUser


class _StatCard(QFrame):
    """Single KPI card — label + value + colour accent."""

    def __init__(self, title: str, value: str, accent: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        title_lbl = QLabel(title)
        title_lbl.setObjectName("SubheadingLabel")
        layout.addWidget(title_lbl)

        value_lbl = QLabel(value)
        value_lbl.setStyleSheet(
            f"font-size: 28px; font-weight: 700; color: {accent}; background: transparent;"
        )
        layout.addWidget(value_lbl)

        # Accent top strip
        self.setStyleSheet(
            f"#Card {{ border-top: 4px solid {accent}; "
            f"background-color: {theme.SURFACE}; "
            f"border-radius: {theme.RADIUS_MD}px; }}"
        )


class DashboardView(QScrollArea):
    """Main dashboard page (Phase 1 — placeholder KPI cards)."""

    def __init__(self, user: SessionUser, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._user = user
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        container.setObjectName("DashboardContainer")
        container.setStyleSheet(f"#DashboardContainer {{ background-color: {theme.BACKGROUND}; }}")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(24)

        # ── Greeting banner ───────────────────────────────────────────────────
        now = datetime.datetime.now()
        hour = now.hour
        greeting = "Good morning" if hour < 12 else ("Good afternoon" if hour < 18 else "Good evening")

        banner = QFrame()
        banner.setObjectName("Card")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(24, 16, 24, 16)

        greet_layout = QVBoxLayout()
        greet_lbl = QLabel(f"{greeting}, {self._user.display_name} 👋")
        greet_lbl.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {theme.TEXT}; background: transparent;"
        )
        greet_layout.addWidget(greet_lbl)

        date_lbl = QLabel(now.strftime("%A, %B %d, %Y"))
        date_lbl.setObjectName("SubheadingLabel")
        greet_layout.addWidget(date_lbl)

        banner_layout.addLayout(greet_layout)
        banner_layout.addStretch()

        self._live_time = QLabel()
        self._live_time.setStyleSheet(
            f"font-size: 22px; font-weight: 600; color: {theme.PRIMARY}; background: transparent;"
        )
        self._update_time()
        banner_layout.addWidget(self._live_time)

        timer = QTimer(self)
        timer.setInterval(1000)
        timer.timeout.connect(self._update_time)
        timer.start()

        layout.addWidget(banner)

        # ── KPI Cards ─────────────────────────────────────────────────────────
        kpi_label = QLabel("Today's Attendance Overview")
        kpi_label.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {theme.TEXT}; background: transparent;"
        )
        layout.addWidget(kpi_label)

        grid = QGridLayout()
        grid.setSpacing(16)

        cards = [
            ("Total Employees", "—", theme.PRIMARY),
            ("Present", "—", theme.SUCCESS),
            ("Absent", "—", theme.DANGER),
            ("Late", "—", theme.WARNING),
            ("On Leave", "—", theme.INFO),
            ("Overtime", "—", theme.TEXT_MUTED),
        ]

        for i, (title, value, accent) in enumerate(cards):
            card = _StatCard(title, value, accent)
            grid.addWidget(card, i // 3, i % 3)

        layout.addLayout(grid)

        # ── Placeholder note ──────────────────────────────────────────────────
        note = QLabel(
            "ℹ  Dashboard data will populate once Workforce and Attendance modules are built (Phases 2–4)."
        )
        note.setObjectName("SubheadingLabel")
        note.setWordWrap(True)
        note.setStyleSheet(
            f"background-color: rgba(107,53,42,0.07); border-radius: 8px; "
            f"padding: 12px 16px; color: {theme.MUTED};"
        )
        layout.addWidget(note)

        layout.addStretch()
        self.setWidget(container)

    def _update_time(self) -> None:
        self._live_time.setText(datetime.datetime.now().strftime("%I:%M:%S %p"))
