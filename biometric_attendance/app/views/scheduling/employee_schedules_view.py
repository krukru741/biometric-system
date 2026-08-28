"""Employee Schedules list view."""
from __future__ import annotations

import datetime as dt

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QDateEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)


class EmployeeSchedulesView(QWidget):
    """View to list employee schedules in a flat table format."""

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("EmployeeSchedulesView")
        self._setup_ui()
        self._connect_signals()
        
        self.vm.load_employees()
        self._apply_filters()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("Employee Schedules")
        title.setObjectName("PageTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        filter_layout = QHBoxLayout()
        
        # Employee filter
        emp_lbl = QLabel("Employee:")
        emp_lbl.setObjectName("FormLabel")
        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumWidth(200)
        self.emp_combo.addItem("All Employees", None)
        
        # Date filters
        today = dt.date.today()
        
        start_lbl = QLabel("Start Date:")
        start_lbl.setObjectName("FormLabel")
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate(today.year, today.month, 1))
        
        end_lbl = QLabel("End Date:")
        end_lbl.setObjectName("FormLabel")
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        
        # Default end date to end of month
        if today.month == 12:
            last_day = dt.date(today.year + 1, 1, 1) - dt.timedelta(days=1)
        else:
            last_day = dt.date(today.year, today.month + 1, 1) - dt.timedelta(days=1)
            
        self.end_date.setDate(QDate(last_day.year, last_day.month, last_day.day))

        self.btn_fetch = QPushButton("Fetch")
        self.btn_fetch.setObjectName("SecondaryButton")
        
        filter_layout.addWidget(emp_lbl)
        filter_layout.addWidget(self.emp_combo)
        filter_layout.addWidget(start_lbl)
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(end_lbl)
        filter_layout.addWidget(self.end_date)
        filter_layout.addWidget(self.btn_fetch)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Emp ID", "Name", "Date", "Shift", "Rest Day", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.schedules_loaded.connect(self._render_table)
        self.vm.error_occurred.connect(self._on_error)
        self.btn_fetch.clicked.connect(self._apply_filters)

    def _on_employees_loaded(self, employees):
        # Preserve current selection if possible
        current_data = self.emp_combo.currentData()
        
        self.emp_combo.clear()
        self.emp_combo.addItem("All Employees", None)
        for emp in employees:
            self.emp_combo.addItem(emp.full_name, emp.id)
            
        if current_data is not None:
            for i in range(self.emp_combo.count()):
                if self.emp_combo.itemData(i) == current_data:
                    self.emp_combo.setCurrentIndex(i)
                    break

    def _apply_filters(self):
        emp_id = self.emp_combo.currentData()
        sd = self.start_date.date()
        ed = self.end_date.date()
        
        start = dt.date(sd.year(), sd.month(), sd.day())
        end = dt.date(ed.year(), ed.month(), ed.day())
        
        if start > end:
            QMessageBox.warning(self, "Invalid Date Range", "Start Date must be before or equal to End Date.")
            return

        self.vm.load_schedules(employee_id=emp_id, start_date=start, end_date=end)

    def _render_table(self, schedules):
        self.table.setRowCount(0)
        for s in schedules:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(s.employee_id_str or ""))
            self.table.setItem(row, 1, QTableWidgetItem(s.employee_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(str(s.date)))
            self.table.setItem(row, 3, QTableWidgetItem(s.shift_name or "-"))
            self.table.setItem(row, 4, QTableWidgetItem("Yes" if s.is_rest_day else "No"))
            self.table.setItem(row, 5, QTableWidgetItem(s.schedule_status.value if s.schedule_status else ""))

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
