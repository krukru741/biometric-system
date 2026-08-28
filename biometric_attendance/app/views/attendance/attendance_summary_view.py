"""Attendance Summary View — placeholder for Phase 4.

Aggregation reports (daily/monthly summaries) will be built in Phase 8 (Reports).
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class AttendanceSummaryView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("Attendance Summary\n\n(Coming in Phase 8 — Reports)")
        lbl.setObjectName("PageTitle")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)
