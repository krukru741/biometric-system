"""Live Attendance View — scan simulator for Phase 4 manual testing.

This panel allows submitting mock attendance events (IN/OUT/BREAK_OUT/BREAK_IN)
and displays the processing result. Duplicate scans produce clear inline feedback
per the Q-approved UX: "Duplicate scan ignored — already recorded at HH:MM:SS".
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, QDateTime, Qt, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.core.enums.attendance import AttendanceEventType
from biometric_attendance.core.dtos.attendance_dtos import ProcessEventResult


class _StatusBanner(QFrame):
    """Inline banner that shows the last scan result (success or duplicate)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("StatusBanner")
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._label = QLabel("")
        self._label.setWordWrap(True)
        self._layout.addWidget(self._label)
        self.hide()

    def show_result(self, result: ProcessEventResult):
        if result.is_duplicate:
            self.setStyleSheet(
                "background-color: #FFF3CD; border: 1px solid #FFC107; border-radius: 6px;"
            )
            self._label.setStyleSheet("color: #856404; font-weight: bold;")
        else:
            status = result.record.status.value
            self.setStyleSheet(
                "background-color: #D4EDDA; border: 1px solid #28A745; border-radius: 6px;"
            )
            self._label.setStyleSheet("color: #155724; font-weight: bold;")
        self._label.setText(result.message)
        self.show()


class LiveAttendanceView(QWidget):
    """Scan simulator for Phase 4 — submit mock attendance events."""

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("LiveAttendanceView")
        self._current_employee_id = None
        self._setup_ui()
        self._connect_signals()
        self.vm.load_employees()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QLabel("Live Attendance — Scan Simulator")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        note = QLabel(
            "⚠️  Phase 4: Mock event source. Submit scans manually to test the attendance engine. "
            "Phase 5 will connect real biometric devices."
        )
        note.setObjectName("FormLabel")
        note.setWordWrap(True)
        note.setStyleSheet("color: #856404; background: #FFF3CD; padding: 8px; border-radius: 4px;")
        layout.addWidget(note)

        # Scan input row
        scan_frame = QFrame()
        scan_frame.setStyleSheet(
            "QFrame { background: white; border: 1px solid #dee2e6; border-radius: 8px; }"
        )
        scan_layout = QVBoxLayout(scan_frame)
        scan_layout.setContentsMargins(16, 16, 16, 16)
        scan_layout.setSpacing(12)

        form_row = QHBoxLayout()

        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumWidth(220)
        form_row.addWidget(QLabel("Employee:"))
        form_row.addWidget(self.emp_combo)

        self.event_type_combo = QComboBox()
        for et in AttendanceEventType:
            self.event_type_combo.addItem(et.value, et)
        form_row.addWidget(QLabel("Event:"))
        form_row.addWidget(self.event_type_combo)

        self.timestamp_edit = QDateTimeEdit()
        self.timestamp_edit.setCalendarPopup(True)
        self.timestamp_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.timestamp_edit.setDateTime(QDateTime.currentDateTime())
        form_row.addWidget(QLabel("Timestamp:"))
        form_row.addWidget(self.timestamp_edit)

        self.now_btn = QPushButton("Now")
        self.now_btn.setObjectName("GhostButton")
        self.now_btn.setFixedWidth(50)
        form_row.addWidget(self.now_btn)

        self.submit_btn = QPushButton("Submit Scan")
        self.submit_btn.setObjectName("PrimaryButton")
        form_row.addWidget(self.submit_btn)

        form_row.addStretch()
        scan_layout.addLayout(form_row)

        # Result banner
        self.banner = _StatusBanner()
        scan_layout.addWidget(self.banner)

        layout.addWidget(scan_frame)

        # Recent events log
        log_label = QLabel("Recent Scans (today)")
        log_label.setObjectName("SubheadingLabel")
        layout.addWidget(log_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Emp ID", "Employee", "Event Type", "Timestamp", "Source", "Verified"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

    def _connect_signals(self):
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.event_processed.connect(self._on_event_processed)
        self.vm.events_loaded.connect(self._render_events)
        self.vm.error_occurred.connect(self._on_error)

        self.submit_btn.clicked.connect(self._on_submit)
        self.now_btn.clicked.connect(
            lambda: self.timestamp_edit.setDateTime(QDateTime.currentDateTime())
        )
        self.emp_combo.currentIndexChanged.connect(self._on_employee_changed)

    def _on_employees_loaded(self, employees):
        self.emp_combo.clear()
        for emp in employees:
            self.emp_combo.addItem(f"{emp.full_name} ({emp.employee_id})", emp.id)
        self._refresh_events()

    def _on_employee_changed(self):
        self._refresh_events()

    def _refresh_events(self):
        emp_id = self.emp_combo.currentData()
        if emp_id:
            today = dt.date.today()
            self.vm.load_recent_events(employee_id=emp_id, date=today)

    def _on_submit(self):
        emp_id = self.emp_combo.currentData()
        if not emp_id:
            QMessageBox.warning(self, "Validation", "Please select an employee.")
            return

        event_type = self.event_type_combo.currentData()
        qdt = self.timestamp_edit.dateTime()
        timestamp = dt.datetime(
            qdt.date().year(), qdt.date().month(), qdt.date().day(),
            qdt.time().hour(), qdt.time().minute(), qdt.time().second()
        )
        self.vm.submit_scan(
            employee_id=emp_id,
            event_type=event_type,
            timestamp=timestamp,
        )

    def _on_event_processed(self, result: ProcessEventResult):
        self.banner.show_result(result)

    def _render_events(self, events):
        self.table.setRowCount(0)
        for ev in reversed(events):  # Most recent first
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(ev.employee_id_str))
            self.table.setItem(row, 1, QTableWidgetItem(ev.employee_name))
            self.table.setItem(row, 2, QTableWidgetItem(ev.event_type.value))
            self.table.setItem(row, 3, QTableWidgetItem(ev.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.setItem(row, 4, QTableWidgetItem(ev.source.value))
            self.table.setItem(row, 5, QTableWidgetItem("Yes" if ev.biometric_verified else "No"))

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
