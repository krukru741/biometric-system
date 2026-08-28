"""Employee Profile View."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QFormLayout,
    QScrollArea,
)

from biometric_attendance.core.dtos.workforce_dtos import EmployeeEntity
from biometric_attendance.app.styles import theme


class EmployeeProfileView(QWidget):
    """Detailed profile view for a single employee with tabs."""

    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._employee: EmployeeEntity | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top Navigation Bar
        top_bar = QWidget()
        top_bar.setStyleSheet(f"background-color: {theme.SURFACE}; border-bottom: 1px solid #E0E0E0;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 10, 20, 10)
        
        self.btn_back = QPushButton("← Back to List")
        self.btn_back.setObjectName("GhostButton")
        self.btn_back.clicked.connect(self.back_requested.emit)
        top_layout.addWidget(self.btn_back)
        
        self.lbl_title = QLabel("Employee Profile")
        self.lbl_title.setObjectName("SubheadingLabel")
        top_layout.addWidget(self.lbl_title)
        top_layout.addStretch()

        layout.addWidget(top_bar)

        # Main Content Layout (Sidebar + Stack)
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Left Sidebar Tabs
        self.tab_list = QListWidget()
        self.tab_list.setFixedWidth(200)
        self.tab_list.addItems([
            "Overview",
            "Attendance",
            "Schedule",
            "Biometrics",
            "Leave",
            "Overtime"
        ])
        self.tab_list.currentRowChanged.connect(self._on_tab_changed)
        content_layout.addWidget(self.tab_list)

        # Right Content Stack
        self.stack = QStackedWidget()
        
        self.page_overview = QWidget()
        self.page_attendance = self._build_placeholder("Attendance History", "Phase 4")
        self.page_schedule = self._build_placeholder("Schedule & Shifts", "Phase 3 / 4")
        self.page_biometrics = self._build_placeholder("Biometric Data", "Phase 5")
        self.page_leave = self._build_placeholder("Leave Records", "Phase 6")
        self.page_overtime = self._build_placeholder("Overtime Records", "Phase 7")
        
        self.stack.addWidget(self.page_overview)
        self.stack.addWidget(self.page_attendance)
        self.stack.addWidget(self.page_schedule)
        self.stack.addWidget(self.page_biometrics)
        self.stack.addWidget(self.page_leave)
        self.stack.addWidget(self.page_overtime)
        
        content_layout.addWidget(self.stack, 1)
        layout.addLayout(content_layout)

    def _build_overview_page(self):
        """Build the overview page dynamically based on current employee data."""
        # Clear existing layout if any
        if self.page_overview.layout():
            QWidget().setLayout(self.page_overview.layout())

        layout = QVBoxLayout(self.page_overview)
        layout.setContentsMargins(0, 0, 0, 0)
        
        if not self._employee:
            return

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        
        content = QWidget()
        form = QFormLayout(content)
        form.setSpacing(12)
        
        emp = self._employee
        
        def _add_section(title):
            lbl = QLabel(f"<b>{title}</b>")
            lbl.setObjectName("FormLabel")
            lbl.setStyleSheet(f"color: {theme.PRIMARY}; font-size: 16px; padding-top: 10px;")
            form.addRow(lbl)

        def _add_field(label, value):
            lbl = QLabel(f"{label}:")
            lbl.setObjectName("FormLabel")
            val = QLabel(str(value) if value else "-")
            form.addRow(lbl, val)

        _add_section("Personal Information")
        _add_field("Employee ID", emp.employee_id)
        _add_field("Full Name", emp.full_name)
        _add_field("Gender", emp.gender)
        _add_field("Birth Date", emp.birth_date)
        _add_field("Email", emp.email)
        _add_field("Phone", emp.phone)
        _add_field("Address", emp.address)

        _add_section("Employment Information")
        _add_field("Department", emp.department_name)
        _add_field("Position", emp.position_name)
        _add_field("Employment Type", emp.employment_type.value if emp.employment_type else "")
        _add_field("Status", emp.status.value if emp.status else "")
        _add_field("Date Hired", emp.date_hired)

        _add_section("Attendance Configuration")
        _add_field("Grace Period", f"{emp.grace_period_mins} mins")
        _add_field("Overtime Eligible", "Yes" if emp.overtime_eligible else "No")
        _add_field("Default Rest Day", emp.rest_day)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _build_placeholder(self, title, phase):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon = QLabel("🚧")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px;")
        
        lbl = QLabel(f"{title}\n\nThis module will be built in {phase}.")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setObjectName("SubheadingLabel")
        
        layout.addWidget(icon)
        layout.addWidget(lbl)
        return w

    def _on_tab_changed(self, index: int):
        self.stack.setCurrentIndex(index)

    def set_employee(self, employee: EmployeeEntity):
        self._employee = employee
        self.lbl_title.setText(f"Employee Profile - {employee.full_name}")
        self._build_overview_page()
        self.tab_list.setCurrentRow(0)
