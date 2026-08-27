"""Add Employee Wizard."""
from __future__ import annotations

import datetime as dt
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QDateEdit,
    QCheckBox,
    QSpinBox,
    QStackedWidget,
    QScrollArea,
    QMessageBox,
)

from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType


class EmployeeWizardDialog(QDialog):
    """A custom 4-step wizard for adding a new employee."""

    def __init__(self, vm, parent=None):
        super().__init__(parent)
        self.vm = vm
        self.setWindowTitle("Add Employee")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header indicating step
        self.step_label = QLabel("Step 1: Personal Information")
        self.step_label.setObjectName("SubheadingLabel")
        layout.addWidget(self.step_label)

        # Stack to hold pages
        self.stack = QStackedWidget()
        
        # Step 1: Personal
        self.page_personal = self._build_personal_page()
        self.stack.addWidget(self.page_personal)
        
        # Step 2: Employment
        self.page_employment = self._build_employment_page()
        self.stack.addWidget(self.page_employment)
        
        # Step 3: Attendance Config
        self.page_attendance = self._build_attendance_page()
        self.stack.addWidget(self.page_attendance)
        
        # Step 4: Biometrics
        self.page_biometrics = self._build_biometrics_page()
        self.stack.addWidget(self.page_biometrics)
        
        layout.addWidget(self.stack, 1)

        # Navigation buttons
        nav_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("GhostButton")
        self.btn_back = QPushButton("Back")
        self.btn_next = QPushButton("Next")
        self.btn_finish = QPushButton("Finish")
        self.btn_finish.setObjectName("PrimaryButton")
        
        nav_layout.addWidget(self.btn_cancel)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_back)
        nav_layout.addWidget(self.btn_next)
        nav_layout.addWidget(self.btn_finish)
        
        layout.addLayout(nav_layout)
        
        self._update_navigation()

    def _build_personal_page(self):
        w = QWidget()
        form = QFormLayout(w)
        
        self.emp_id_input = QLineEdit()
        self.fname_input = QLineEdit()
        self.mname_input = QLineEdit()
        self.lname_input = QLineEdit()
        self.suffix_input = QLineEdit()
        self.birth_date_input = QDateEdit()
        self.birth_date_input.setCalendarPopup(True)
        self.birth_date_input.setDate(QDate(1990, 1, 1))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other", "Prefer not to say"])
        self.phone_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        form.addRow(self._label("Employee ID *"), self.emp_id_input)
        form.addRow(self._label("First Name *"), self.fname_input)
        form.addRow(self._label("Middle Name"), self.mname_input)
        form.addRow(self._label("Last Name *"), self.lname_input)
        form.addRow(self._label("Suffix"), self.suffix_input)
        form.addRow(self._label("Birth Date"), self.birth_date_input)
        form.addRow(self._label("Gender"), self.gender_combo)
        form.addRow(self._label("Phone"), self.phone_input)
        form.addRow(self._label("Email"), self.email_input)
        form.addRow(self._label("Address"), self.address_input)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(w)
        return scroll

    def _build_employment_page(self):
        w = QWidget()
        form = QFormLayout(w)
        
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

        form.addRow(self._label("Department"), self.dept_combo)
        form.addRow(self._label("Position"), self.pos_combo)
        form.addRow(self._label("Employment Type"), self.type_combo)
        form.addRow(self._label("Date Hired"), self.date_hired_input)
        form.addRow(self._label("Employment Status"), self.status_combo)
        form.addRow(self._label("Supervisor"), self.supervisor_combo)
        
        return w

    def _build_attendance_page(self):
        w = QWidget()
        form = QFormLayout(w)
        
        self.grace_spin = QSpinBox()
        self.grace_spin.setRange(0, 120)
        self.ot_check = QCheckBox()
        
        self.rest_day_combo = QComboBox()
        self.rest_day_combo.addItems(["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        
        form.addRow(self._label("Grace Period (mins)"), self.grace_spin)
        form.addRow(self._label("Overtime Eligible"), self.ot_check)
        form.addRow(self._label("Default Rest Day"), self.rest_day_combo)
        
        return w

    def _build_biometrics_page(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("👆")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        
        lbl = QLabel("Biometric enrollment will be completed in Phase 5.\nYou can safely finish adding this employee now.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(icon)
        layout.addWidget(lbl)
        
        return w

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text + ":")
        lbl.setObjectName("FormLabel")
        return lbl

    def _connect_signals(self):
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_back.clicked.connect(self._go_back)
        self.btn_next.clicked.connect(self._go_next)
        self.btn_finish.clicked.connect(self._on_finish)
        
        # Load external data (departments, positions, supervisors)
        self.vm.departments_loaded.connect(self._on_departments_loaded)
        self.vm.positions_loaded.connect(self._on_positions_loaded)
        self.vm.employees_loaded.connect(self._on_employees_loaded)
        self.vm.load_data()

    def _on_departments_loaded(self, depts):
        self.dept_combo.clear()
        self.dept_combo.addItem("None", -1)
        for dept in depts:
            self.dept_combo.addItem(dept.name, dept.id)

    def _on_positions_loaded(self, positions):
        self.pos_combo.clear()
        self.pos_combo.addItem("None", -1)
        for pos in positions:
            self.pos_combo.addItem(pos.name, pos.id)

    def _on_employees_loaded(self, employees):
        self.supervisor_combo.clear()
        self.supervisor_combo.addItem("None", -1)
        for emp in employees:
            self.supervisor_combo.addItem(emp.full_name, emp.id)

    def _update_navigation(self):
        idx = self.stack.currentIndex()
        titles = [
            "Step 1: Personal Information",
            "Step 2: Employment Information",
            "Step 3: Attendance Config",
            "Step 4: Biometric Enrollment"
        ]
        self.step_label.setText(titles[idx])
        
        self.btn_back.setVisible(idx > 0)
        self.btn_next.setVisible(idx < self.stack.count() - 1)
        self.btn_finish.setVisible(idx == self.stack.count() - 1)

    def _go_back(self):
        idx = self.stack.currentIndex()
        if idx > 0:
            self.stack.setCurrentIndex(idx - 1)
            self._update_navigation()

    def _go_next(self):
        idx = self.stack.currentIndex()
        
        # Validation for Step 1
        if idx == 0:
            if not self.emp_id_input.text().strip():
                QMessageBox.warning(self, "Validation Error", "Employee ID is required.")
                return
            if not self.fname_input.text().strip():
                QMessageBox.warning(self, "Validation Error", "First Name is required.")
                return
            if not self.lname_input.text().strip():
                QMessageBox.warning(self, "Validation Error", "Last Name is required.")
                return
        
        if idx < self.stack.count() - 1:
            self.stack.setCurrentIndex(idx + 1)
            self._update_navigation()

    def _on_finish(self):
        self.accept()

    def get_form_data(self):
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
