"""Attendance Records View — shows processed daily attendance records.

Includes a 'Generate Absent Records' button for manual absent-record creation
(per Q3 decision; automation deferred to Phase 10 but must be complete for Phase 8 Reports).
"""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
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

from biometric_attendance.core.enums.attendance import AttendanceStatus


_STATUS_COLORS = {
    AttendanceStatus.PRESENT: "#28A745",
    AttendanceStatus.LATE: "#FFC107",
    AttendanceStatus.ABSENT: "#DC3545",
    AttendanceStatus.ON_LEAVE: "#17A2B8",
    AttendanceStatus.REST_DAY: "#6C757D",
    AttendanceStatus.HOLIDAY: "#6F42C1",
    AttendanceStatus.HALF_DAY: "#FD7E14",
    AttendanceStatus.INCOMPLETE: "#DC3545",
    AttendanceStatus.UNDERTIME: "#E83E8C",
    AttendanceStatus.OVERTIME: "#20C997",
}


class AttendanceRecordsView(QWidget):
    """Attendance Records table with filters and absent-generation."""

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("AttendanceRecordsView")
        self._setup_ui()
        self._connect_signals()
        self.vm.load_employees()
        self._apply_filters()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("Attendance Records")
        title.setObjectName("PageTitle")
        self.generate_absent_btn = QPushButton("Generate Absent Records")
        self.generate_absent_btn.setObjectName("SecondaryButton")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.generate_absent_btn)
        layout.addLayout(header)

        # Filters
        today = dt.date.today()
        filter_layout = QHBoxLayout()

        self.emp_combo = QComboBox()
        self.emp_combo.addItem("All Employees", None)
        self.emp_combo.setMinimumWidth(180)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate(today.year, today.month, 1))

        if today.month == 12:
            last = dt.date(today.year + 1, 1, 1) - dt.timedelta(days=1)
        else:
            last = dt.date(today.year, today.month + 1, 1) - dt.timedelta(days=1)
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate(last.year, last.month, last.day))

        self.fetch_btn = QPushButton("Fetch")
        self.fetch_btn.setObjectName("SecondaryButton")

        filter_layout.addWidget(QLabel("Employee:"))
        filter_layout.addWidget(self.emp_combo)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(self.fetch_btn)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "Date", "Emp ID", "Employee", "Time In", "Break Out", "Break In", "Time Out",
            "Worked", "Late", "Undertime", "Overtime", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table, 1)

    def _connect_signals(self):
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.records_loaded.connect(self._render_table)
        self.vm.absent_generated.connect(self._on_absent_generated)
        self.vm.error_occurred.connect(self._on_error)
        self.fetch_btn.clicked.connect(self._apply_filters)
        self.generate_absent_btn.clicked.connect(self._on_generate_absent)

    def _on_employees_loaded(self, employees):
        current = self.emp_combo.currentData()
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("All Employees", None)
        for emp in employees:
            self.emp_combo.addItem(emp.full_name, emp.id)
        self.emp_combo.blockSignals(False)

    def _apply_filters(self):
        emp_id = self.emp_combo.currentData()
        sd = self.start_date.date()
        ed = self.end_date.date()
        start = dt.date(sd.year(), sd.month(), sd.day())
        end = dt.date(ed.year(), ed.month(), ed.day())
        if start > end:
            QMessageBox.warning(self, "Validation", "Start date must be ≤ end date.")
            return
        self.vm.load_records(start_date=start, end_date=end, employee_id=emp_id)

    def _render_table(self, records):
        self.table.setRowCount(0)
        for rec in records:
            row = self.table.rowCount()
            self.table.insertRow(row)

            def _fmt_dt(v):
                return v.strftime("%H:%M:%S") if v else "-"

            self.table.setItem(row, 0, QTableWidgetItem(str(rec.date)))
            self.table.setItem(row, 1, QTableWidgetItem(rec.employee_id_str))
            self.table.setItem(row, 2, QTableWidgetItem(rec.employee_name))
            self.table.setItem(row, 3, QTableWidgetItem(_fmt_dt(rec.time_in)))
            self.table.setItem(row, 4, QTableWidgetItem(_fmt_dt(rec.break_out)))
            self.table.setItem(row, 5, QTableWidgetItem(_fmt_dt(rec.break_in)))
            self.table.setItem(row, 6, QTableWidgetItem(_fmt_dt(rec.time_out)))
            self.table.setItem(row, 7, QTableWidgetItem(f"{rec.worked_minutes} min"))
            self.table.setItem(row, 8, QTableWidgetItem(f"{rec.late_minutes} min"))
            self.table.setItem(row, 9, QTableWidgetItem(f"{rec.undertime_minutes} min"))
            self.table.setItem(row, 10, QTableWidgetItem(f"{rec.overtime_minutes} min"))

            status_item = QTableWidgetItem(rec.status.value)
            color = _STATUS_COLORS.get(rec.status, "#6C757D")
            status_item.setForeground(Qt.GlobalColor.white)
            from PySide6.QtGui import QColor, QBrush
            status_item.setBackground(QBrush(QColor(color)))
            self.table.setItem(row, 11, status_item)

    def _on_generate_absent(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Generate Absent Records")
        layout = QVBoxLayout(dialog)
        
        info = QLabel(
            "Generate ABSENT records for all active employees with no attendance on a specific date.\n\n"
            "Employees with an existing record (any status) on that date will be skipped."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        form = QFormLayout()
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        form.addRow("Target Date:", date_edit)
        layout.addLayout(form)
        
        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(dialog.accept)
        bb.rejected.connect(dialog.reject)
        layout.addWidget(bb)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            sd = date_edit.date()
            target = dt.date(sd.year(), sd.month(), sd.day())
            self.vm.generate_absent_records(target)

    def _on_absent_generated(self, count: int):
        QMessageBox.information(
            self, "Done", f"{count} ABSENT record(s) generated."
        )

    def _on_error(self, message: str):
        QMessageBox.critical(self, "Error", message)
