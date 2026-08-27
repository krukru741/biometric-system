"""Schedule Calendar View — monthly grid with click-to-assign and bulk assign."""
from __future__ import annotations

import calendar
import datetime as dt
from typing import Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.viewmodels.scheduling_vms import ScheduleCalendarViewModel
from biometric_attendance.core.dtos.scheduling_dtos import (
    EmployeeScheduleEntity,
    ShiftTemplateEntity,
)
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity


_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class AssignDayDialog(QDialog):
    """Dialog to assign or clear a shift for one employee on one date."""

    def __init__(
        self,
        parent,
        date: dt.date,
        employee: EmployeeEntity,
        shifts: list[ShiftTemplateEntity],
        existing: EmployeeScheduleEntity | None,
    ):
        super().__init__(parent)
        self.setWindowTitle(f"Schedule — {employee.full_name} — {date}")
        self.setMinimumWidth(360)
        self._result: dict | None = None

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.shift_combo = QComboBox()
        self.shift_combo.addItem("— No Shift —", -1)
        for s in shifts:
            self.shift_combo.addItem(s.name + (" 🌙" if s.is_overnight else ""), s.id)
        lbl = QLabel("Shift")
        lbl.setObjectName("FormLabel")
        form.addRow(lbl, self.shift_combo)

        self.rest_check = QCheckBox("Mark as Rest Day")
        form.addRow("", self.rest_check)

        layout.addLayout(form)

        bb = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        ok_btn = bb.button(QDialogButtonBox.StandardButton.Ok)
        ok_btn.setObjectName("PrimaryButton")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        layout.addWidget(bb)

        # Pre-fill
        if existing:
            if existing.is_rest_day:
                self.rest_check.setChecked(True)
            elif existing.shift_template_id is not None:
                for i in range(self.shift_combo.count()):
                    if self.shift_combo.itemData(i) == existing.shift_template_id:
                        self.shift_combo.setCurrentIndex(i)
                        break

        # Rest day overrides shift selection
        self.rest_check.toggled.connect(lambda on: self.shift_combo.setEnabled(not on))

    def get_data(self) -> dict:
        is_rest = self.rest_check.isChecked()
        shift_id = self.shift_combo.currentData() if not is_rest else None
        return {
            "shift_template_id": shift_id if shift_id != -1 else None,
            "is_rest_day": is_rest,
        }


class ScheduleCalendarView(QWidget):
    """Monthly calendar grid + bulk-assign panel."""

    def __init__(self, vm: ScheduleCalendarViewModel, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setObjectName("ScheduleCalendarView")

        self._schedules: list[EmployeeScheduleEntity] = []
        self._employees: list[EmployeeEntity] = []
        self._departments: list[DepartmentEntity] = []
        self._shifts: list[ShiftTemplateEntity] = []
        self._filtered_employee: Optional[EmployeeEntity] = None

        today = dt.date.today()
        self._year = today.year
        self._month = today.month

        self._setup_ui()
        self._connect_signals()
        self.vm.load_supporting_data()
        self.vm.load_month(self._year, self._month)

    # ── UI setup ──────────────────────────────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Title + month navigation
        nav_row = QHBoxLayout()
        title = QLabel("Schedule Calendar")
        title.setObjectName("PageTitle")
        nav_row.addWidget(title)
        nav_row.addStretch()

        self.prev_btn = QPushButton("‹")
        self.prev_btn.setFixedWidth(36)
        self.month_label = QLabel()
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setMinimumWidth(150)
        self.next_btn = QPushButton("›")
        self.next_btn.setFixedWidth(36)

        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.month_label)
        nav_row.addWidget(self.next_btn)
        layout.addLayout(nav_row)

        # Filters
        filter_row = QHBoxLayout()
        emp_lbl = QLabel("Employee:")
        emp_lbl.setObjectName("FormLabel")
        self.emp_combo = QComboBox()
        self.emp_combo.setMinimumWidth(200)
        dept_lbl = QLabel("Department:")
        dept_lbl.setObjectName("FormLabel")
        self.dept_combo = QComboBox()
        self.dept_combo.setMinimumWidth(150)
        filter_row.addWidget(emp_lbl)
        filter_row.addWidget(self.emp_combo)
        filter_row.addWidget(dept_lbl)
        filter_row.addWidget(self.dept_combo)
        filter_row.addStretch()
        layout.addLayout(filter_row)

        # Calendar grid
        self.cal_table = QTableWidget()
        self.cal_table.setColumnCount(7)
        self.cal_table.setHorizontalHeaderLabels(_WEEKDAYS)
        self.cal_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.cal_table.verticalHeader().setVisible(False)
        self.cal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cal_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.cal_table.setMinimumHeight(260)
        layout.addWidget(self.cal_table, 1)

        # Bulk assign panel
        bulk_box = QGroupBox("Bulk Assign")
        bulk_layout = QFormLayout(bulk_box)

        self.bulk_dept_combo = QComboBox()
        lbl = QLabel("Department")
        lbl.setObjectName("FormLabel")
        bulk_layout.addRow(lbl, self.bulk_dept_combo)

        self.bulk_shift_combo = QComboBox()
        lbl = QLabel("Shift")
        lbl.setObjectName("FormLabel")
        bulk_layout.addRow(lbl, self.bulk_shift_combo)

        date_row = QHBoxLayout()
        self.bulk_start = QDateEdit()
        self.bulk_start.setDisplayFormat("yyyy-MM-dd")
        self.bulk_start.setCalendarPopup(True)
        self.bulk_start.setDate(QDate.currentDate())
        self.bulk_end = QDateEdit()
        self.bulk_end.setDisplayFormat("yyyy-MM-dd")
        self.bulk_end.setCalendarPopup(True)
        self.bulk_end.setDate(QDate.currentDate().addDays(6))
        date_row.addWidget(QLabel("From:"))
        date_row.addWidget(self.bulk_start)
        date_row.addWidget(QLabel("To:"))
        date_row.addWidget(self.bulk_end)
        lbl = QLabel("Date Range")
        lbl.setObjectName("FormLabel")
        bulk_layout.addRow(lbl, date_row)

        self.bulk_assign_btn = QPushButton("Assign")
        self.bulk_assign_btn.setObjectName("PrimaryButton")
        bulk_layout.addRow("", self.bulk_assign_btn)

        layout.addWidget(bulk_box)

        self._update_month_label()

    # ── Signal wiring ─────────────────────────────────────────────────────────

    def _connect_signals(self):
        self.prev_btn.clicked.connect(self._on_prev_month)
        self.next_btn.clicked.connect(self._on_next_month)
        self.emp_combo.currentIndexChanged.connect(self._on_employee_filter_changed)
        self.dept_combo.currentIndexChanged.connect(self._on_dept_filter_changed)
        self.cal_table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.bulk_assign_btn.clicked.connect(self._on_bulk_assign)

        self.vm.schedules_loaded.connect(self._on_schedules_loaded)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.shifts_loaded.connect(self._on_shifts_loaded)
        self.vm.bulk_assign_done.connect(self._on_bulk_done)
        self.vm.error_occurred.connect(lambda m: QMessageBox.critical(self, "Error", m))

    # ── Navigation ────────────────────────────────────────────────────────────

    def _on_prev_month(self):
        if self._month == 1:
            self._month = 12
            self._year -= 1
        else:
            self._month -= 1
        self._update_month_label()
        self.vm.load_month(self._year, self._month)

    def _on_next_month(self):
        if self._month == 12:
            self._month = 1
            self._year += 1
        else:
            self._month += 1
        self._update_month_label()
        self.vm.load_month(self._year, self._month)

    def _update_month_label(self):
        name = calendar.month_name[self._month]
        self.month_label.setText(f"{name} {self._year}")

    # ── Data handlers ─────────────────────────────────────────────────────────

    def _on_employees_loaded(self, employees: list):
        self._employees = employees
        current_id = self.emp_combo.currentData()
        self.emp_combo.clear()
        self.emp_combo.addItem("All Employees", -1)
        for e in employees:
            self.emp_combo.addItem(e.full_name, e.id)
        # Restore
        for i in range(self.emp_combo.count()):
            if self.emp_combo.itemData(i) == current_id:
                self.emp_combo.setCurrentIndex(i)
                break

    def _on_departments_loaded(self, departments: list):
        self._departments = departments
        self.bulk_dept_combo.clear()
        self.bulk_dept_combo.addItem("All Departments", -1)
        for d in departments:
            self.bulk_dept_combo.addItem(d.name, d.id)

        current = self.dept_combo.currentData()
        self.dept_combo.clear()
        self.dept_combo.addItem("All Departments", -1)
        for d in departments:
            self.dept_combo.addItem(d.name, d.id)
        for i in range(self.dept_combo.count()):
            if self.dept_combo.itemData(i) == current:
                self.dept_combo.setCurrentIndex(i)
                break

    def _on_shifts_loaded(self, shifts: list):
        self._shifts = shifts
        self.bulk_shift_combo.clear()
        for s in shifts:
            self.bulk_shift_combo.addItem(s.name + (" 🌙" if s.is_overnight else ""), s.id)

    def _on_schedules_loaded(self, schedules: list):
        self._schedules = schedules
        self._render_calendar()

    def _on_employee_filter_changed(self):
        emp_id = self.emp_combo.currentData()
        self._filtered_employee = next((e for e in self._employees if e.id == emp_id), None)
        self._render_calendar()

    def _on_dept_filter_changed(self):
        # Refresh employee combo filtered by dept
        dept_id = self.dept_combo.currentData()
        self.emp_combo.blockSignals(True)
        self.emp_combo.clear()
        self.emp_combo.addItem("All Employees", -1)
        for e in self._employees:
            if dept_id == -1 or e.department_id == dept_id:
                self.emp_combo.addItem(e.full_name, e.id)
        self.emp_combo.blockSignals(False)
        self._filtered_employee = None
        self._render_calendar()

    # ── Calendar rendering ────────────────────────────────────────────────────

    def _render_calendar(self):
        """Populate the QTableWidget with one cell per calendar day."""
        # Determine filter
        emp_id = self.emp_combo.currentData()

        # Build schedule lookup: {(employee_id, date): entity}
        sched_lookup: dict[tuple[int, dt.date], EmployeeScheduleEntity] = {}
        for s in self._schedules:
            if emp_id == -1 or s.employee_id == emp_id:
                sched_lookup[(s.employee_id, s.date)] = s

        # Build calendar grid
        cal = calendar.monthcalendar(self._year, self._month)
        self.cal_table.setRowCount(len(cal))

        for week_idx, week in enumerate(cal):
            for day_idx, day_num in enumerate(week):
                if day_num == 0:
                    item = QTableWidgetItem("")
                    item.setBackground(Qt.GlobalColor.lightGray)
                    self.cal_table.setItem(week_idx, day_idx, item)
                    continue

                cell_date = dt.date(self._year, self._month, day_num)

                # Collect schedules for this day
                day_scheds = [
                    s for (eid, d), s in sched_lookup.items() if d == cell_date
                ]

                lines = [str(day_num)]
                for s in day_scheds:
                    if s.is_rest_day:
                        lines.append("REST")
                    elif s.shift_name:
                        lines.append(s.shift_name)
                    if emp_id == -1 and len(day_scheds) > 1:
                        # multiple employees — show count summary
                        lines = [str(day_num), f"{len(day_scheds)} assigned"]
                        break

                cell_text = "\n".join(lines)
                item = QTableWidgetItem(cell_text)
                item.setData(Qt.ItemDataRole.UserRole, (day_num, day_scheds))

                # Highlight today
                if cell_date == dt.date.today():
                    from biometric_attendance.app.styles import theme
                    item.setBackground(Qt.GlobalColor.yellow)

                self.cal_table.setItem(week_idx, day_idx, item)

        self.cal_table.resizeRowsToContents()

    # ── Click handler ─────────────────────────────────────────────────────────

    def _on_cell_double_clicked(self, row: int, col: int):
        item = self.cal_table.item(row, col)
        if item is None:
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        if data is None:
            return
        day_num, day_scheds = data
        cell_date = dt.date(self._year, self._month, day_num)

        emp_id = self.emp_combo.currentData()
        if emp_id == -1:
            # Must filter to a single employee first
            QMessageBox.information(
                self,
                "Select Employee",
                "Please select a specific employee from the filter to assign a schedule.",
            )
            return

        employee = next((e for e in self._employees if e.id == emp_id), None)
        if employee is None:
            return

        existing = next((s for s in day_scheds if s.employee_id == emp_id), None)
        dialog = AssignDayDialog(self, cell_date, employee, self._shifts, existing)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            d = dialog.get_data()
            self.vm.assign_schedule(
                employee_id=emp_id,
                date=cell_date,
                shift_template_id=d["shift_template_id"],
                is_rest_day=d["is_rest_day"],
            )

    # ── Bulk assign ───────────────────────────────────────────────────────────

    def _on_bulk_assign(self):
        dept_id = self.bulk_dept_combo.currentData()
        shift_id = self.bulk_shift_combo.currentData()
        if shift_id is None:
            QMessageBox.warning(self, "Validation Error", "Please select a shift template.")
            return

        qs = self.bulk_start.date()
        qe = self.bulk_end.date()
        start = dt.date(qs.year(), qs.month(), qs.day())
        end = dt.date(qe.year(), qe.month(), qe.day())
        if end < start:
            QMessageBox.warning(self, "Validation Error", "End date must be >= Start date.")
            return

        dept_id_val = dept_id if dept_id != -1 else None
        self.vm.bulk_assign(
            department_id=dept_id_val,
            employee_ids=None,
            shift_template_id=shift_id,
            start_date=start,
            end_date=end,
        )

    def _on_bulk_done(self, count: int):
        QMessageBox.information(
            self,
            "Bulk Assign Complete",
            f"{count} schedule(s) assigned successfully.\nExisting schedules and rest days were skipped.",
        )
