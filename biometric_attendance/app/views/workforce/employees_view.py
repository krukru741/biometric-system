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
    QDateEdit,
    QCheckBox,
    QSpinBox,
)

from biometric_attendance.app.viewmodels.workforce_vms import EmployeesViewModel
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity, PositionEntity
from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType


class AddEmployeeDialog(QDialog):
    """Single-page form to add an employee."""

    def __init__(self, vm: EmployeesViewModel, parent: QWidget | None = None):
        super().__init__(parent)
        self.vm = vm
        self.setWindowTitle("Add Employee")
        self.setMinimumWidth(500)
        
        self.departments: list[DepartmentEntity] = []
        self.positions: list[PositionEntity] = []

        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # -- Personal Info --
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
        
        # -- Employment Info --
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
        
        # -- Attendance Config --
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
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        
        # Re-emit signals if data is already loaded in vm
        self.vm.load_data()

    def _on_departments_loaded(self, depts: list[DepartmentEntity]) -> None:
        self.dept_combo.clear()
        self.dept_combo.addItem("None", -1)
        for dept in depts:
            self.dept_combo.addItem(dept.name, dept.id)

    def _on_positions_loaded(self, positions: list[PositionEntity]) -> None:
        self.pos_combo.clear()
        self.pos_combo.addItem("None", -1)
        for pos in positions:
            self.pos_combo.addItem(pos.name, pos.id)

    def get_form_data(self) -> dict[str, Any]:
        """Extract data to pass to viewmodel."""
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
    """View to list Employees and open Add Dialog."""

    def __init__(self, view_model: EmployeesViewModel, parent: QWidget | None = None):
        super().__init__(parent)
        self.vm = view_model
        self.setObjectName("EmployeesView")
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        self.vm.load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Employees")
        title.setObjectName("PageTitle")
        
        self.add_btn = QPushButton("Add Employee")
        self.add_btn.setObjectName("PrimaryButton")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.add_btn)
        
        layout.addLayout(header_layout)

        # Filters (Placeholder for future)
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search Employees...")
        self.search_input.setMaximumWidth(300)
        filter_layout.addWidget(self.search_input)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Emp ID", "Name", "Department", "Position", "Type", "Status", "Email"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def _connect_signals(self) -> None:
        self.add_btn.clicked.connect(self._on_add_clicked)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.error_occurred.connect(self._on_error)
        
        self.search_input.textChanged.connect(self._on_search)

    def _on_add_clicked(self) -> None:
        dialog = AddEmployeeDialog(self.vm, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_form_data()
            if not data["employee_id"] or not data["first_name"] or not data["last_name"]:
                QMessageBox.warning(self, "Validation Error", "Employee ID, First Name, and Last Name are required.")
                return
                
            self.vm.create_employee(data)

    def _on_employees_loaded(self, employees: list[EmployeeEntity]) -> None:
        # Cache for search
        self._all_employees = employees
        self._render_table(employees)
        
    def _on_search(self, text: str) -> None:
        if not hasattr(self, '_all_employees'):
            return
            
        text = text.lower()
        filtered = [
            emp for emp in self._all_employees
            if text in emp.employee_id.lower() or text in emp.full_name.lower() or text in (emp.email or "").lower()
        ]
        self._render_table(filtered)

    def _render_table(self, employees: list[EmployeeEntity]) -> None:
        self.table.setRowCount(0)
        for emp in employees:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(emp.employee_id))
            self.table.setItem(row, 1, QTableWidgetItem(emp.full_name))
            self.table.setItem(row, 2, QTableWidgetItem(emp.department_name or "N/A"))
            self.table.setItem(row, 3, QTableWidgetItem(emp.position_name or "N/A"))
            self.table.setItem(row, 4, QTableWidgetItem(emp.employment_type.value))
            self.table.setItem(row, 5, QTableWidgetItem(emp.status.value))
            self.table.setItem(row, 6, QTableWidgetItem(emp.email))

    def _on_error(self, message: str) -> None:
        QMessageBox.critical(self, "Error", message)
