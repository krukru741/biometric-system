"""AppShell — main window after login.

Contains Sidebar (left) + TopBar + QStackedWidget (right).
Each page is lazily constructed on first navigation.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.styles import theme
from biometric_attendance.app.widgets.sidebar import Sidebar
from biometric_attendance.app.widgets.topbar import TopBar
from biometric_attendance.app.views.dashboard_view import DashboardView
from biometric_attendance.app.views.workforce.departments_view import DepartmentsView
from biometric_attendance.app.views.workforce.positions_view import PositionsView
from biometric_attendance.app.views.workforce.employees_view import EmployeesView
from biometric_attendance.app.viewmodels.scheduling_vms import (
    ShiftTemplatesViewModel,
    HolidaysViewModel,
    ScheduleCalendarViewModel,
    EmployeeSchedulesViewModel,
)
from biometric_attendance.app.views.scheduling.shift_templates_view import ShiftTemplatesView
from biometric_attendance.app.views.scheduling.holidays_view import HolidaysView
from biometric_attendance.app.views.scheduling.schedule_calendar_view import ScheduleCalendarView
from biometric_attendance.app.views.scheduling.employee_schedules_view import EmployeeSchedulesView
from biometric_attendance.app.viewmodels.attendance_vms import (
    AttendanceLiveViewModel,
    AttendanceRecordsViewModel,
    AttendanceCorrectionsViewModel,
)
from biometric_attendance.app.views.attendance.live_attendance_view import LiveAttendanceView
from biometric_attendance.app.views.attendance.attendance_records_view import AttendanceRecordsView
from biometric_attendance.app.views.attendance.attendance_corrections_view import AttendanceCorrectionsView
from biometric_attendance.app.views.attendance.attendance_summary_view import AttendanceSummaryView

from biometric_attendance.app.viewmodels.workforce_vms import DepartmentsViewModel, PositionsViewModel, EmployeesViewModel
from biometric_attendance.core.dtos.auth_dtos import SessionUser
from biometric_attendance.app.container import AppContainer

# Human-readable page titles keyed by page_key
_PAGE_TITLES: dict[str, str] = {
    "dashboard": "Dashboard",
    "employees": "Employees",
    "departments": "Departments",
    "positions": "Positions",
    "biometric_enrollment": "Biometric Enrollment",
    "biometric_devices": "Biometric Devices",
    "biometric_sync": "Biometric Synchronization",
    "attendance_live": "Live Attendance",
    "attendance_records": "Attendance Records",
    "attendance_corrections": "Attendance Corrections",
    "attendance_summary": "Daily Summary",
    "shift_templates": "Shift Templates",
    "employee_schedules": "Employee Schedules",
    "schedule_calendar": "Schedule Calendar",
    "holidays": "Holidays",
    "leave_requests": "Leave Requests",
    "leave_approvals": "Leave Approvals",
    "leave_types": "Leave Types",
    "overtime_requests": "Overtime Requests",
    "overtime_approvals": "Overtime Approvals",
    "reports": "Reports",
    "admin_users": "User Management",
    "admin_roles": "Roles & Permissions",
    "audit_logs": "Audit Logs",
    "system_settings": "System Settings",
    "database_backup": "Database Backup",
}


class _PlaceholderPage(QWidget):
    """Generic placeholder used for pages not yet implemented."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {theme.BACKGROUND};")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)

        icon = QLabel("🚧")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 48px; background: transparent;")
        layout.addWidget(icon)

        lbl = QLabel(f"{title}\n\nThis module will be built in an upcoming phase.")
        lbl.setObjectName("SubheadingLabel")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)


class AppShell(QMainWindow):
    """Main application window post-login.

    Signals:
        logout_requested: relayed from Sidebar to main.py for screen switching.
    """

    logout_requested = Signal()

    def __init__(self, user: SessionUser, container: AppContainer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._user = user
        self._container = container
        self._pages: dict[str, QWidget] = {}

        self.setWindowTitle("Biometric Attendance Tracking System")
        self.setMinimumSize(1100, 680)
        self._build_ui()
        # Navigate to Dashboard on start
        self._navigate("dashboard")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = Sidebar(self._user)
        self._sidebar.page_requested.connect(self._navigate)
        self._sidebar.logout_requested.connect(self.logout_requested.emit)
        root_layout.addWidget(self._sidebar)

        # ── Right area ────────────────────────────────────────────────────────
        right = QWidget()
        right.setObjectName("AppShellRight")
        right.setStyleSheet(f"#AppShellRight {{ background-color: {theme.BACKGROUND}; }}")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self._topbar = TopBar(self._user)
        right_layout.addWidget(self._topbar)

        self._stack = QStackedWidget()
        self._stack.setObjectName("AppShellStack")
        self._stack.setStyleSheet(f"#AppShellStack {{ background-color: {theme.BACKGROUND}; }}")
        right_layout.addWidget(self._stack, 1)

        root_layout.addWidget(right, 1)

    def _navigate(self, page_key: str) -> None:
        """Switch the stacked widget to the given page, building it if needed."""
        if page_key not in self._pages:
            self._pages[page_key] = self._build_page(page_key)
            self._stack.addWidget(self._pages[page_key])

        self._stack.setCurrentWidget(self._pages[page_key])
        self._sidebar.set_active(page_key)
        title = _PAGE_TITLES.get(page_key, page_key.replace("_", " ").title())
        self._topbar.set_page_title(title)

    def _build_page(self, page_key: str) -> QWidget:
        if page_key == "dashboard":
            return DashboardView(self._user)
        elif page_key == "departments":
            vm = DepartmentsViewModel(self._container.workforce_service())
            return DepartmentsView(vm)
        elif page_key == "positions":
            vm = PositionsViewModel(self._container.workforce_service())
            return PositionsView(vm)
        elif page_key == "employees":
            vm = EmployeesViewModel(self._container.workforce_service())
            return EmployeesView(vm)
        elif page_key == "shift_templates":
            vm = ShiftTemplatesViewModel(self._container.scheduling_service())
            return ShiftTemplatesView(vm)
        elif page_key == "holidays":
            vm = HolidaysViewModel(self._container.scheduling_service())
            return HolidaysView(vm)
        elif page_key == "schedule_calendar":
            vm = ScheduleCalendarViewModel(self._container.scheduling_service())
            return ScheduleCalendarView(vm)
        elif page_key == "employee_schedules":
            vm = EmployeeSchedulesViewModel(self._container.scheduling_service())
            return EmployeeSchedulesView(vm)
        elif page_key == "attendance_live":
            vm = AttendanceLiveViewModel(
                event_service=self._container.attendance_event_service(),
                employee_repository=self._container.employee_repository(),
            )
            return LiveAttendanceView(vm)
        elif page_key == "attendance_records":
            vm = AttendanceRecordsViewModel(
                record_repository=self._container.attendance_record_repository(),
                employee_repository=self._container.employee_repository(),
            )
            return AttendanceRecordsView(vm)
        elif page_key == "attendance_corrections":
            vm = AttendanceCorrectionsViewModel(
                correction_service=self._container.attendance_correction_service(),
                employee_repository=self._container.employee_repository(),
                record_repository=self._container.attendance_record_repository(),
            )
            return AttendanceCorrectionsView(vm, logged_in_user_id=self._user.id)
        elif page_key == "attendance_summary":
            return AttendanceSummaryView()
        title = _PAGE_TITLES.get(page_key, page_key.replace("_", " ").title())
        return _PlaceholderPage(title)
