"""View for managing Employees."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QScrollArea,
    QCheckBox,
    QSpinBox,
)

from biometric_attendance.app.viewmodels.workforce_vms import EmployeesViewModel
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity, PositionEntity
from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType

_ALL_STATUSES = "All"


class EmployeeFormDialog(QDialog):
    """Add or Edit employee form dialog."""

    def __init__(self, vm, parent=None, employee=None):
        super().__init__(parent)
        self.vm = vm
        self._employee = employee
        is_edit = employee is not None

        self.setWindowTitle("Edit Employee" if is_edit else "Add Employee")
        self.setMinimumWidth(500)

        self._setup_ui(is_edit)
        self._connect_signals()

    def _setup_ui(self, is_edit):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)

        header = QLabel("<b>Personal Information</b>")
        header.setObjectName("FormLabel")
        form_layout.addRow(header)

        self.emp_id_input = QLineEdit()
        lbl = QLabel("Employee ID *:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.emp_id_input)

        self.fname_input = QLineEdit()
        lbl = QLabel("First Name *:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.fname_input)

        self.mname_input = QLineEdit()
        lbl = QLabel("Middle Name:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.mname_input)

        self.lname_input = QLineEdit()
        lbl = QLabel("Last Name *:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.lname_input)

        self.email_input = QLineEdit()
        lbl = QLabel("Email:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.email_input)

        header = QLabel("<b><br>Employment Information</b>")
        header.setObjectName("FormLabel")
        form_layout.addRow(header)

        self.dept_combo = QComboBox()
        lbl = QLabel("Department:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.dept_combo)

        self.pos_combo = QComboBox()
        lbl = QLabel("Position:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.pos_combo)

        self.type_combo = QComboBox()
        for t in EmploymentType:
            self.type_combo.addItem(t.value, t)
        lbl = QLabel("Employment Type:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.type_combo)

        header = QLabel("<b><br>Attendance Config</b>")
        header.setObjectName("FormLabel")
        form_layout.addRow(header)

        self.grace_spin = QSpinBox()
        self.grace_spin.setRange(0, 120)
        lbl = QLabel("Grace Period (mins):")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.grace_spin)

        self.ot_check = QCheckBox()
        lbl = QLabel("Overtime Eligible:")
        lbl.setObjectName("FormLabel")
        form_layout.addRow(lbl, self.ot_check)

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

        btn_label = "Update Employee" if is_edit else "Add Employee"
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.save_btn = QPushButton(btn_label)
        self.save_btn.setObjectName("PrimaryButton")
        self.button_box.addButton(self.save_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _connect_signals(self):
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        self.vm.load_data()

    def _on_departments_loaded(self, depts):
        self.dept_combo.clear()
        self.dept_combo.addItem("None", -1)
        for dept in depts:
            self.dept_combo.addItem(dept.name, dept.id)
        if self._employee and self._employee.department_id is not None:
            for i in range(self.dept_combo.count()):
                if self.dept_combo.itemData(i) == self._employee.department_id:
                    self.dept_combo.setCurrentIndex(i)
                    break

    def _on_positions_loaded(self, positions):
        self.pos_combo.clear()
        self.pos_combo.addItem("None", -1)
        for pos in positions:
            self.pos_combo.addItem(pos.name, pos.id)
        if self._employee and self._employee.position_id is not None:
            for i in range(self.pos_combo.count()):
                if self.pos_combo.itemData(i) == self._employee.position_id:
                    self.pos_combo.setCurrentIndex(i)
                    break

    def prefill(self):
        """Pre-fill the form with the employee current data."""
        emp = self._employee
        if emp is None:
            return
        self.emp_id_input.setText(emp.employee_id or "")
        self.fname_input.setText(emp.first_name or "")
        self.mname_input.setText(emp.middle_name or "")
        self.lname_input.setText(emp.last_name or "")
        self.email_input.setText(emp.email or "")
        self.grace_spin.setValue(emp.grace_period_mins or 0)
        self.ot_check.setChecked(emp.overtime_eligible or False)
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == emp.employment_type:
                self.type_combo.setCurrentIndex(i)
                break

    def get_form_data(self):
        dept_id = self.dept_combo.currentData()
        pos_id = self.pos_combo.currentData()
        return {
            "employee_id": self.emp_id_input.text().strip(),
            "first_name": self.fname_input.text().strip(),
            "middle_name": self.mname_input.text().strip(),
            "last_name": self.lname_input.text().strip(),
            "email": self.email_input.text().strip(),
            "department_id": dept_id if dept_id != -1 else None,
            "position_id": pos_id if pos_id != -1 else None,
            "employment_type": self.type_combo.currentData(),
            "grace_period_mins": self.grace_spin.value(),
            "overtime_eligible": self.ot_check.isChecked(),
        }


class EmployeesView(QWidget):
    """View to list, add, edit, archive and filter Employees."""

    def __init__(self, view_model, parent=None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("EmployeesView")
        self._all_employees = []
        self._setup_ui()
        self._connect_signals()
        self.vm.load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        header_layout = QHBoxLayout()
        title = QLabel("Employees")
        title.setObjectName("PageTitle")
        self.add_btn = QPushButton("Add Employee")
        self.add_btn.setObjectName("PrimaryButton")
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.add_btn)
        layout.addLayout(header_layout)

        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Employees...")
        self.search_input.setMaximumWidth(300)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Active", EmploymentStatus.ACTIVE)
        self.status_filter.addItem("Inactive", EmploymentStatus.INACTIVE)
        self.status_filter.addItem("Archived", EmploymentStatus.ARCHIVED)
        self.status_filter.addItem("All", _ALL_STATUSES)
        self.status_filter.setCurrentIndex(0)  # Default: Active only

        status_lbl = QLabel("Status:")
        status_lbl.setObjectName("FormLabel")
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(status_lbl)
        filter_layout.addWidget(self.status_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Emp ID", "Name", "Department", "Position", "Type", "Status", "Email", "Actions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.error_occurred.connect(self._on_error)
        self.search_input.textChanged.connect(self._apply_filters)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)

    def _on_add_clicked(self):
        dialog = EmployeeFormDialog(self.vm, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()
            if not data["employee_id"] or not data["first_name"] or not data["last_name"]:
                QMessageBox.warning(self, "Validation Error", "Employee ID, First Name, and Last Name are required.")
                return
            self.vm.create_employee(data)

    def _on_edit_clicked(self, employee):
        dialog = EmployeeFormDialog(self.vm, self, employee=employee)
        dialog.prefill()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()
            if not data["employee_id"] or not data["first_name"] or not data["last_name"]:
                QMessageBox.warning(self, "Validation Error", "Employee ID, First Name, and Last Name are required.")
                return
            self.vm.update_employee(employee.id, data)

    def _on_archive_clicked(self, employee):
        reply = QMessageBox.question(
            self,
            "Archive Employee",
            "Archive {} {}?\n\nThey will no longer appear in active lists. "
            "This does not delete their records.".format(employee.first_name, employee.last_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.vm.archive_employee(employee.id)

    def _on_employees_loaded(self, employees):
        self._all_employees = employees
        self._apply_filters()

    def _apply_filters(self):
        """Filter by status dropdown then by search text — search operates within current status filter."""
        status_value = self.status_filter.currentData()
        search_text = self.search_input.text().strip().lower()

        filtered = self._all_employees

        if status_value is not _ALL_STATUSES:
            filtered = [e for e in filtered if e.status == status_value]

        if search_text:
            filtered = [
                e for e in filtered
                if search_text in (e.employee_id or "").lower()
                or search_text in (e.full_name or "").lower()
                or search_text in (e.email or "").lower()
            ]

        self._render_table(filtered)

    def _render_table(self, employees):
        self.table.setRowCount(0)
        for emp in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(emp.employee_id or ""))
            self.table.setItem(row, 1, QTableWidgetItem(emp.full_name or ""))
            self.table.setItem(row, 2, QTableWidgetItem(emp.department_name or "N/A"))
            self.table.setItem(row, 3, QTableWidgetItem(emp.position_name or "N/A"))
            self.table.setItem(row, 4, QTableWidgetItem(emp.employment_type.value if emp.employment_type else ""))
            self.table.setItem(row, 5, QTableWidgetItem(emp.status.value if emp.status else ""))
            self.table.setItem(row, 6, QTableWidgetItem(emp.email or ""))

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.clicked.connect(lambda checked, e=emp: self._on_edit_clicked(e))

            archive_btn = QPushButton("Archive")
            archive_btn.setObjectName("GhostButton")
            archive_btn.setEnabled(emp.status != EmploymentStatus.ARCHIVED)
            archive_btn.clicked.connect(lambda checked, e=emp: self._on_archive_clicked(e))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(archive_btn)
            self.table.setCellWidget(row, 7, actions_widget)

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
