"""Sidebar navigation widget.

Reads the current user's permissions and only shows nav items
the user is authorised to access (per 02-AUTHENTICATION-AUTHORIZATION.md).
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from biometric_attendance.app.styles import theme
from biometric_attendance.core.dtos.auth_dtos import SessionUser
from biometric_attendance.core.enums.permissions import Permission


@dataclass
class NavItem:
    label: str
    page_key: str
    permission: Permission | None = None  # None = always visible

@dataclass
class NavSection:
    title: str
    items: list[NavItem]


# Navigation definition — grouped into collapsible sections
_NAV_ITEMS: list[NavItem | NavSection] = [
    NavItem("Dashboard", "dashboard", Permission.DASHBOARD_VIEW),
    NavSection("WORKFORCE", [
        NavItem("Employees", "employees", Permission.EMPLOYEE_VIEW),
        NavItem("Departments", "departments", Permission.EMPLOYEE_VIEW),
        NavItem("Positions", "positions", Permission.EMPLOYEE_VIEW),
    ]),
    NavSection("BIOMETRICS", [
        NavItem("Enrollment", "biometric_enrollment", Permission.BIOMETRIC_ENROLL),
        NavItem("Devices", "biometric_devices", Permission.BIOMETRIC_MANAGE),
        NavItem("Synchronization", "biometric_sync", Permission.BIOMETRIC_MANAGE),
    ]),
    NavSection("ATTENDANCE", [
        NavItem("Live Attendance", "attendance_live", Permission.ATTENDANCE_VIEW),
        NavItem("Records", "attendance_records", Permission.ATTENDANCE_VIEW),
        NavItem("Corrections", "attendance_corrections", Permission.ATTENDANCE_CORRECT),
        NavItem("Daily Summary", "attendance_summary", Permission.ATTENDANCE_VIEW),
    ]),
    NavSection("SCHEDULING", [
        NavItem("Shift Templates", "shift_templates", Permission.SCHEDULE_VIEW),
        NavItem("Calendar", "schedule_calendar", Permission.SCHEDULE_VIEW),
        NavItem("Holidays", "holidays", Permission.SCHEDULE_VIEW),
    ]),
    NavSection("LEAVE", [
        NavItem("Requests", "leave_requests", Permission.LEAVE_VIEW),
        NavItem("Approvals", "leave_approvals", Permission.LEAVE_APPROVE),
        NavItem("Leave Types", "leave_types", Permission.LEAVE_VIEW),
    ]),
    NavSection("OVERTIME", [
        NavItem("Requests", "overtime_requests", Permission.OVERTIME_VIEW),
        NavItem("Approvals", "overtime_approvals", Permission.OVERTIME_APPROVE),
    ]),
    NavSection("REPORTS", [
        NavItem("Reports", "reports", Permission.REPORTS_VIEW),
    ]),
    NavSection("ADMINISTRATION", [
        NavItem("Users", "admin_users", Permission.USERS_MANAGE),
        NavItem("Roles & Permissions", "admin_roles", Permission.USERS_MANAGE),
        NavItem("Audit Logs", "audit_logs", Permission.AUDIT_VIEW),
        NavItem("System Settings", "system_settings", Permission.SETTINGS_MANAGE),
        NavItem("Database Backup", "database_backup", Permission.BACKUP_MANAGE),
    ]),
]


class _CollapsibleSection(QWidget):
    """A section that can be expanded/collapsed."""
    
    def __init__(self, title: str, items: list[NavItem], user: SessionUser, sidebar: Sidebar) -> None:
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        self.title_text = title
        self.is_expanded = False

        self.header_btn = QPushButton(f"{self.title_text}  ▶")
        self.header_btn.setObjectName("SidebarSectionHeader")
        self.header_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_btn.clicked.connect(self.toggle)
        self.layout.addWidget(self.header_btn)

        self.content_widget = QWidget()
        content_outer = QHBoxLayout(self.content_widget)
        content_outer.setContentsMargins(14, 2, 0, 4)
        content_outer.setSpacing(8)

        guide = QFrame()
        guide.setObjectName("SidebarIndentGuide")
        content_outer.addWidget(guide)

        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(1)
        content_outer.addLayout(self.content_layout)
        
        has_visible_children = False
        for item in items:
            if item.permission and not user.has_permission(item.permission):
                continue
            btn = sidebar._make_nav_button(item, sub=True)
            self.content_layout.addWidget(btn)
            sidebar._buttons[item.page_key] = btn
            sidebar._section_map[item.page_key] = self
            has_visible_children = True
            
        self.layout.addWidget(self.content_widget)
        self.content_widget.setVisible(self.is_expanded)
        
        if not has_visible_children:
            self.hide() # hide entire section if no permissions

    def toggle(self) -> None:
        self.is_expanded = not self.is_expanded
        self.content_widget.setVisible(self.is_expanded)
        icon = "▼" if self.is_expanded else "▶"
        self.header_btn.setText(f"{self.title_text}  {icon}")

    def expand(self) -> None:
        if not self.is_expanded:
            self.toggle()


class Sidebar(QFrame):
    """Left navigation panel.

    Emits page_requested(page_key) when a nav button is clicked.
    """

    page_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self, user: SessionUser, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._user = user
        self._buttons: dict[str, QPushButton] = {}
        self._section_map: dict[str, _CollapsibleSection] = {}
        self._active_key: str = ""
        self.setObjectName("Sidebar")
        self.setFixedWidth(theme.SIDEBAR_WIDTH)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 16, 10, 10)
        outer.setSpacing(0)

        # ── App branding ──────────────────────────────────────────────────────
        title = QLabel("BATS")
        title.setObjectName("SidebarAppTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)

        subtitle = QLabel("Biometric Attendance")
        subtitle.setObjectName("SidebarAppSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(subtitle)

        outer.addSpacing(12)

        # ── Scrollable nav ────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("background: transparent;")

        nav_widget = QWidget()
        nav_widget.setStyleSheet("background: transparent;")
        nav_layout = QVBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(2)

        for item in _NAV_ITEMS:
            if isinstance(item, NavSection):
                section = _CollapsibleSection(item.title, item.items, self._user, self)
                nav_layout.addWidget(section)
            else:
                if item.permission and not self._user.has_permission(item.permission):
                    continue
                btn = self._make_nav_button(item)
                nav_layout.addWidget(btn)
                self._buttons[item.page_key] = btn

        nav_layout.addStretch()
        scroll.setWidget(nav_widget)
        outer.addWidget(scroll, 1)

        # ── Logout ────────────────────────────────────────────────────────────
        outer.addSpacing(8)
        logout_btn = QPushButton("⏻  Logout")
        logout_btn.setObjectName("SidebarNavButton")
        logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        logout_btn.clicked.connect(self.logout_requested.emit)
        outer.addWidget(logout_btn)

    def _make_nav_button(self, item: NavItem, sub: bool = False) -> QPushButton:
        btn = QPushButton(item.label)
        btn.setObjectName("SidebarSubNavButton" if sub else "SidebarNavButton")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setProperty("active", "false")
        btn.clicked.connect(lambda _checked=False, key=item.page_key: self._on_nav_clicked(key))
        return btn

    def _on_nav_clicked(self, page_key: str) -> None:
        self.set_active(page_key)
        self.page_requested.emit(page_key)

    def set_active(self, page_key: str) -> None:
        """Highlight the active nav button and expand its section."""
        # Un-highlight old
        if self._active_key and self._active_key in self._buttons:
            self._buttons[self._active_key].setProperty("active", "false")
            self._buttons[self._active_key].style().unpolish(self._buttons[self._active_key])
            self._buttons[self._active_key].style().polish(self._buttons[self._active_key])

        self._active_key = page_key
        
        # Expand parent section if it exists
        if page_key in self._section_map:
            self._section_map[page_key].expand()
            
        # Highlight new
        if page_key in self._buttons:
            self._buttons[page_key].setProperty("active", "true")
            self._buttons[page_key].style().unpolish(self._buttons[page_key])
            self._buttons[page_key].style().polish(self._buttons[page_key])
