"""Accessible, paginated attendance screen built from shared Qt components."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import QDate, QTimer, Qt
from PySide6.QtWidgets import (QComboBox, QDateEdit, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget)
from biometric_attendance.app.widgets.components import Column, ContentState, FilterBar, PageHeader, RecordTable, plain_label


class AttendanceRecordsView(QWidget):
    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self._page = 0
        self._has_more = False
        self._loading = False
        self.setObjectName("AttendanceRecordsView")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.generate_absent_btn = QPushButton("Generate Absent Records")
        self.generate_absent_btn.setObjectName("SecondaryButton")
        layout.addWidget(PageHeader("Attendance Records", "Review daily hours, exceptions, and attendance status.", action=self.generate_absent_btn))
        filters = FilterBar()
        self.emp_combo = QComboBox()
        self.emp_combo.addItem("All Employees", None)
        today = QDate.currentDate()
        self.start_date = QDateEdit(QDate(today.year(), today.month(), 1))
        self.end_date = QDateEdit(QDate(today.year(), today.month(), today.daysInMonth()))
        for edit in (self.start_date, self.end_date):
            edit.setCalendarPopup(True)
            edit.setDisplayFormat("dd MMM yyyy")
        filters.add_field("&Employee", self.emp_combo)
        filters.add_field("&From", self.start_date)
        filters.add_field("&To", self.end_date)
        self.fetch_btn = QPushButton("&Apply filters")
        self.fetch_btn.setObjectName("PrimaryButton")
        filters.add_action(self.fetch_btn)
        layout.addWidget(filters)
        self.validation = plain_label("")
        self.validation.setObjectName("InlineError")
        self.validation.hide()
        layout.addWidget(self.validation)
        time_format = lambda value: value.strftime("%H:%M:%S")
        columns = [Column("Date", lambda r: r.date), Column("Employee ID", lambda r: r.employee_id_str),
                   Column("Employee", lambda r: r.employee_name, width=200)]
        for title, field in [("Time In", "time_in"), ("Break Out", "break_out"), ("Break In", "break_in"), ("Time Out", "time_out")]:
            columns.append(Column(title, lambda r, f=field: getattr(r, f), time_format))
        for title, field in [("Worked", "worked_minutes"), ("Late", "late_minutes"), ("Undertime", "undertime_minutes"), ("Overtime", "overtime_minutes")]:
            columns.append(Column(title, lambda r, f=field: getattr(r, f), lambda value: f"{value} min"))
        columns.append(Column("Status", lambda r: r.status.value))
        self.table = RecordTable(columns, name="Attendance records", row_key=lambda r: r.id)
        self.table.setAccessibleDescription("100 records per page. Column headers sort the current page.")
        self.content_state = ContentState(self.table)
        layout.addWidget(self.content_state, 1)
        footer = QHBoxLayout()
        self.result_label = plain_label("Loading attendance…")
        self.previous_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.previous_btn.setAccessibleName("Previous attendance page")
        self.next_btn.setAccessibleName("Next attendance page")
        footer.addWidget(self.result_label, 1)
        footer.addWidget(self.previous_btn)
        footer.addWidget(self.next_btn)
        layout.addLayout(footer)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.records_loaded.connect(self._render_table)
        self.vm.page_loaded.connect(self._on_page_loaded)
        self.vm.loading_changed.connect(self._on_loading)
        self.vm.absent_generated.connect(self._on_absent_generated)
        self.vm.error_occurred.connect(self._on_error)
        self.fetch_btn.clicked.connect(lambda: self._apply_filters())
        self.previous_btn.clicked.connect(lambda: self._apply_filters(self._page - 1))
        self.next_btn.clicked.connect(lambda: self._apply_filters(self._page + 1))
        self.generate_absent_btn.clicked.connect(self._on_generate_absent)
        self.content_state.action_requested.connect(self._retry)
        self.start_date.dateChanged.connect(self._filters_changed)
        self.end_date.dateChanged.connect(self._filters_changed)
        self.emp_combo.currentIndexChanged.connect(self._filters_changed)
        self.content_state.show_state("loading", "Loading attendance…")
        QTimer.singleShot(0, self._retry)

    def _retry(self):
        self.vm.load_employees()
        self._apply_filters()

    def _on_employees_loaded(self, employees):
        current = self.emp_combo.currentData()
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("All Employees", None)
        for emp in employees:
            self.emp_combo.addItem(f"{emp.full_name} ({emp.employee_id})", emp.id)
        index = self.emp_combo.findData(current)
        self.emp_combo.setCurrentIndex(max(0, index))
        self.emp_combo.blockSignals(False)

    def _apply_filters(self, page=0):
        start = self.start_date.date().toPython()
        end = self.end_date.date().toPython()
        if start > end:
            self.validation.setText("Choose an end date on or after the start date.")
            self.validation.show()
            self.end_date.setAccessibleDescription(self.validation.text())
            self.end_date.setFocus()
            return
        self.validation.hide()
        self.end_date.setAccessibleDescription("")
        self.vm.load_records(start_date=start, end_date=end, employee_id=self.emp_combo.currentData(), page=max(0, page))

    def _filters_changed(self, *_):
        self.previous_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.result_label.setText("Filters changed. Select Apply filters to update results.")

    def _on_loading(self, loading):
        self._loading = loading
        self.fetch_btn.setEnabled(not loading)
        for control in (self.start_date, self.end_date, self.emp_combo):
            control.setEnabled(not loading)
        self.generate_absent_btn.setEnabled(not loading)
        self.previous_btn.setEnabled(not loading and self._page > 0)
        self.next_btn.setEnabled(not loading and self._has_more)
        if loading:
            self.content_state.show_state("loading", "Loading attendance…", "Your selected filters will be applied.")
            self.result_label.setText("Loading attendance…")

    def _on_page_loaded(self, page, has_more):
        self._page, self._has_more = page, has_more
        self.previous_btn.setEnabled(page > 0)
        self.next_btn.setEnabled(has_more)

    def _render_table(self, records):
        self.table.set_rows(records)
        self.result_label.setText(f"Page {self._page + 1} · {len(records)} records · Sort applies to this page")
        if records:
            self.content_state.show_content()
        else:
            self.content_state.show_state("empty", "No attendance records", "Try a different employee or date range.")

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
        self._apply_filters()
        QMessageBox.information(self, "Records generated", f"{count} absent record(s) generated.")

    def _on_error(self, message: str):
        self.content_state.show_state("error", "Attendance unavailable", message, action="Try again")
        self.result_label.setText("Attendance could not be loaded")
