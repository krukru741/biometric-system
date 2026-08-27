"""Permission constants used throughout the system.

All 20 granular permissions from 02-AUTHENTICATION-AUTHORIZATION.md §5.
"""
from enum import StrEnum


class Permission(StrEnum):
    # Dashboard
    DASHBOARD_VIEW = "dashboard.view"

    # Employees
    EMPLOYEE_VIEW = "employee.view"
    EMPLOYEE_CREATE = "employee.create"
    EMPLOYEE_EDIT = "employee.edit"
    EMPLOYEE_ARCHIVE = "employee.archive"

    # Attendance
    ATTENDANCE_VIEW = "attendance.view"
    ATTENDANCE_CORRECT = "attendance.correct"
    ATTENDANCE_APPROVE = "attendance.approve"
    ATTENDANCE_KIOSK = "attendance.kiosk"

    # Biometrics
    BIOMETRIC_ENROLL = "biometric.enroll"
    BIOMETRIC_MANAGE = "biometric.manage"

    # Scheduling
    SCHEDULE_VIEW = "schedule.view"
    SCHEDULE_CREATE = "schedule.create"
    SCHEDULE_EDIT = "schedule.edit"

    # Leave
    LEAVE_VIEW = "leave.view"
    LEAVE_CREATE = "leave.create"
    LEAVE_APPROVE = "leave.approve"

    # Overtime
    OVERTIME_VIEW = "overtime.view"
    OVERTIME_CREATE = "overtime.create"
    OVERTIME_APPROVE = "overtime.approve"

    # Reports
    REPORTS_VIEW = "reports.view"
    REPORTS_EXPORT = "reports.export"

    # Administration
    USERS_MANAGE = "users.manage"
    SETTINGS_MANAGE = "settings.manage"
    AUDIT_VIEW = "audit.view"
    BACKUP_MANAGE = "backup.manage"
