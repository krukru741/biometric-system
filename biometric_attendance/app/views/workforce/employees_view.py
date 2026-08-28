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
    QStackedWidget,
)

from biometric_attendance.app.viewmodels.workforce_vms import EmployeesViewModel
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity, PositionEntity
from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType
from biometric_attendance.app.views.workforce.employee_wizard import EmployeeWizardDialog

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
        self.fname_input = QLineEdit()
        self.mname_input = QLineEdit()
        self.lname_input = QLineEdit()
        self.suffix_input = QLineEdit()
        
        from PySide6.QtWidgets import QDateEdit, QComboBox
        from PySide6.QtCore import QDate
        import datetime as dt
        
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate(1990, 1, 1))
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other", "Prefer not to say"])
        
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        form_layout.addRow(self._label("Employee ID *"), self.emp_id_input)
        form_layout.addRow(self._label("First Name *"), self.fname_input)
        form_layout.addRow(self._label("Middle Name"), self.mname_input)
        form_layout.addRow(self._label("Last Name *"), self.lname_input)
        form_layout.addRow(self._label("Suffix"), self.suffix_input)
        form_layout.addRow(self._label("Birth Date"), self.birth_date_input)
        form_layout.addRow(self._label("Gender"), self.gender_combo)
        form_layout.addRow(self._label("Phone"), self.phone_input)
        form_layout.addRow(self._label("Email"), self.email_input)
        form_layout.addRow(self._label("Address"), self.address_input)

        header = QLabel("<b><br>Employment Information</b>")
        header.setObjectName("FormLabel")
        form_layout.addRow(header)

        self.dept_combo = QComboBox()
        self.pos_combo = QComboBox()
        self.type_combo = QComboBox()
        for t in EmploymentType:
            self.type_combo.addItem(t.value, t)
            
        self.date_hired_input = QDateEdit()
        self.date_hired_input.setCalendarPopup(True)
        self.date_hired_input.setDate(QDate.currentDate())
        
        self.status_combo = QComboBox()
        for s in EmploymentStatus:
            self.status_combo.addItem(s.value, s)
            
        self.supervisor_combo = QComboBox()

        form_layout.addRow(self._label("Department"), self.dept_combo)
        form_layout.addRow(self._label("Position"), self.pos_combo)
        form_layout.addRow(self._label("Employment Type"), self.type_combo)
        form_layout.addRow(self._label("Date Hired"), self.date_hired_input)
        form_layout.addRow(self._label("Employment Status"), self.status_combo)
        form_layout.addRow(self._label("Supervisor"), self.supervisor_combo)

        header = QLabel("<b><br>Attendance Config</b>")
        header.setObjectName("FormLabel")
        form_layout.addRow(header)

        self.grace_spin = QSpinBox()
        self.grace_spin.setRange(0, 120)
        self.ot_check = QCheckBox()
        
        self.rest_day_combo = QComboBox()
        self.rest_day_combo.addItems(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        
        form_layout.addRow(self._label("Grace Period (mins)"), self.grace_spin)
        form_layout.addRow(self._label("Overtime Eligible"), self.ot_check)
        form_layout.addRow(self._label("Default Rest Day"), self.rest_day_combo)

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
        
    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text + ":")
        lbl.setObjectName("FormLabel")
        return lbl

    def _connect_signals(self):
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
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

    def _on_employees_loaded(self, employees):
        self.supervisor_combo.clear()
        self.supervisor_combo.addItem("None", -1)
        for emp in employees:
            if self._employee and emp.id == self._employee.id:
                continue # Cannot be own supervisor
            self.supervisor_combo.addItem(emp.full_name, emp.id)
        if self._employee and self._employee.supervisor_id is not None:
            for i in range(self.supervisor_combo.count()):
                if self.supervisor_combo.itemData(i) == self._employee.supervisor_id:
                    self.supervisor_combo.setCurrentIndex(i)
                    break

    def prefill(self):
        """Pre-fill the form with the employee current data."""
        from PySide6.QtCore import QDate
        emp = self._employee
        if emp is None:
            return
        self.emp_id_input.setText(emp.employee_id or "")
        self.fname_input.setText(emp.first_name or "")
        self.mname_input.setText(emp.middle_name or "")
        self.lname_input.setText(emp.last_name or "")
        self.suffix_input.setText(emp.suffix or "")
        self.email_input.setText(emp.email or "")
        self.phone_input.setText(emp.phone or "")
        self.address_input.setText(emp.address or "")
        
        if emp.birth_date:
            self.birth_date_input.setDate(QDate(emp.birth_date.year, emp.birth_date.month, emp.birth_date.day))
            
        if emp.date_hired:
            self.date_hired_input.setDate(QDate(emp.date_hired.year, emp.date_hired.month, emp.date_hired.day))
            
        self.grace_spin.setValue(emp.grace_period_mins or 0)
        self.ot_check.setChecked(emp.overtime_eligible or False)
        
        self.gender_combo.setCurrentText(emp.gender or "")
        self.rest_day_combo.setCurrentText(emp.rest_day or "Sunday")
        
        for i in range(self.type_combo.count()):
            if self.type_combo.itemData(i) == emp.employment_type:
                self.type_combo.setCurrentIndex(i)
                break
                
        for i in range(self.status_combo.count()):
            if self.status_combo.itemData(i) == emp.status:
                self.status_combo.setCurrentIndex(i)
                break

    def get_form_data(self):
        import datetime as dt
        dept_id = self.dept_combo.currentData()
        pos_id = self.pos_combo.currentData()
        sup_id = self.supervisor_combo.currentData()
        
        birth_d = self.birth_date_input.date()
        date_h = self.date_hired_input.date()
        
        return {
            "employee_id": self.emp_id_input.text().strip(),
            "first_name": self.fname_input.text().strip(),
            "middle_name": self.mname_input.text().strip(),
            "last_name": self.lname_input.text().strip(),
            "suffix": self.suffix_input.text().strip(),
            "birth_date": dt.date(birth_d.year(), birth_d.month(), birth_d.day()),
            "gender": self.gender_combo.currentText(),
            "phone": self.phone_input.text().strip(),
            "email": self.email_input.text().strip(),
            "address": self.address_input.text().strip(),
            "department_id": dept_id if dept_id != -1 else None,
            "position_id": pos_id if pos_id != -1 else None,
            "employment_type": self.type_combo.currentData(),
            "date_hired": dt.date(date_h.year(), date_h.month(), date_h.day()),
            "status": self.status_combo.currentData(),
            "supervisor_id": sup_id if sup_id != -1 else None,
            "grace_period_mins": self.grace_spin.value(),
            "overtime_eligible": self.ot_check.isChecked(),
            "rest_day": self.rest_day_combo.currentText(),
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
        from biometric_attendance.app.views.workforce.employee_profile_view import EmployeeProfileView
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)
        
        # 0: List Page
        self.list_page = QWidget()
        layout = QVBoxLayout(self.list_page)
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
        self.search_input.setMaximumWidth(200)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Active", EmploymentStatus.ACTIVE)
        self.status_filter.addItem("Inactive", EmploymentStatus.INACTIVE)
        self.status_filter.addItem("Archived", EmploymentStatus.ARCHIVED)
        self.status_filter.addItem("All", _ALL_STATUSES)
        self.status_filter.setCurrentIndex(0)

        self.dept_filter = QComboBox()
        self.dept_filter.addItem("All Departments", -1)
        self.dept_filter.setMinimumWidth(150)

        self.pos_filter = QComboBox()
        self.pos_filter.addItem("All Positions", -1)
        self.pos_filter.setMinimumWidth(150)

        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.status_filter)
        filter_layout.addWidget(QLabel("Dept:"))
        filter_layout.addWidget(self.dept_filter)
        filter_layout.addWidget(QLabel("Pos:"))
        filter_layout.addWidget(self.pos_filter)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["Emp ID", "Name", "Department", "Position", "Type", "Status", "Email", "Actions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(7, 240)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        
        self.stack.addWidget(self.list_page)
        
        # 1: Profile Page
        self.profile_page = EmployeeProfileView()
        self.profile_page.back_requested.connect(self._on_back_to_list)
        self.stack.addWidget(self.profile_page)

    def _connect_signals(self):
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        self.vm.error_occurred.connect(self._on_error)
        self.search_input.textChanged.connect(self._apply_filters)
        self.status_filter.currentIndexChanged.connect(self._apply_filters)
        self.dept_filter.currentIndexChanged.connect(self._apply_filters)
        self.pos_filter.currentIndexChanged.connect(self._apply_filters)

    def _on_back_to_list(self):
        self.stack.setCurrentIndex(0)

    def _on_add_clicked(self):
        dialog = EmployeeWizardDialog(self.vm, self)
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

    def _on_view_clicked(self, employee):
        self.profile_page.set_employee(employee)
        self.stack.setCurrentIndex(1)

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

    def _on_departments_loaded(self, departments):
        current = self.dept_filter.currentData()
        self.dept_filter.blockSignals(True)
        self.dept_filter.clear()
        self.dept_filter.addItem("All Departments", -1)
        for d in departments:
            self.dept_filter.addItem(d.name, d.id)
        
        for i in range(self.dept_filter.count()):
            if self.dept_filter.itemData(i) == current:
                self.dept_filter.setCurrentIndex(i)
                break
        self.dept_filter.blockSignals(False)

    def _on_positions_loaded(self, positions):
        current = self.pos_filter.currentData()
        self.pos_filter.blockSignals(True)
        self.pos_filter.clear()
        self.pos_filter.addItem("All Positions", -1)
        for p in positions:
            self.pos_filter.addItem(p.name, p.id)
        
        for i in range(self.pos_filter.count()):
            if self.pos_filter.itemData(i) == current:
                self.pos_filter.setCurrentIndex(i)
                break
        self.pos_filter.blockSignals(False)

    def _apply_filters(self):
        status_value = self.status_filter.currentData()
        dept_value = self.dept_filter.currentData()
        pos_value = self.pos_filter.currentData()
        search_text = self.search_input.text().strip().lower()

        filtered = self._all_employees

        if status_value is not _ALL_STATUSES:
            filtered = [e for e in filtered if e.status == status_value]
        if dept_value != -1 and dept_value is not None:
            filtered = [e for e in filtered if e.department_id == dept_value]
        if pos_value != -1 and pos_value is not None:
            filtered = [e for e in filtered if e.position_id == pos_value]

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
            
            view_btn = QPushButton("View")
            view_btn.setObjectName("SecondaryButton")
            view_btn.setMinimumWidth(50)
            view_btn.clicked.connect(lambda checked, e=emp: self._on_view_clicked(e))

            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("SecondaryButton")
            edit_btn.setMinimumWidth(50)
            edit_btn.clicked.connect(lambda checked, e=emp: self._on_edit_clicked(e))

            archive_btn = QPushButton("Archive")
            archive_btn.setObjectName("GhostButton")
            archive_btn.setEnabled(emp.status != EmploymentStatus.ARCHIVED)
            archive_btn.clicked.connect(lambda checked, e=emp: self._on_archive_clicked(e))

            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(archive_btn)
            self.table.setCellWidget(row, 7, actions_widget)
        self.table.setColumnWidth(7, 240)

    def _on_error(self, message):
        QMessageBox.critical(self, "Error", message)
