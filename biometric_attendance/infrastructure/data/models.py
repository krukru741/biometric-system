"""SQLAlchemy ORM models for Phase 1 (Users / Roles / Permissions).

Tables:
    users, roles, permissions, user_roles, role_permissions

Also contains seed_roles_and_permissions() which is called once on
first startup to populate the static lookup data (roles + permissions).
No default user is seeded — that happens through the setup wizard.
"""
from __future__ import annotations

import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from biometric_attendance.core.enums.permissions import Permission
from biometric_attendance.core.enums.roles import RoleName
from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType
from biometric_attendance.core.enums.scheduling import HolidayType, ScheduleStatus
from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    AttendanceSource,
    AttendanceStatus,
    CorrectionType,
    CorrectionStatus,
)


class Base(DeclarativeBase):
    pass


# ── Association tables ────────────────────────────────────────────────────────

user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions_table = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Models ────────────────────────────────────────────────────────────────────


class PermissionModel(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel", secondary=role_permissions_table, back_populates="permissions"
    )


class RoleModel(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    permissions: Mapped[list[PermissionModel]] = relationship(
        "PermissionModel", secondary=role_permissions_table, back_populates="roles"
    )
    users: Mapped[list[UserModel]] = relationship(
        "UserModel", secondary=user_roles_table, back_populates="roles"
    )


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    roles: Mapped[list[RoleModel]] = relationship(
        "RoleModel", secondary=user_roles_table, back_populates="users", lazy="joined"
    )


# ── Seed data ─────────────────────────────────────────────────────────────────

# Default role → permissions mapping (from 02-AUTHENTICATION-AUTHORIZATION.md)
_ROLE_PERMISSION_MAP: dict[RoleName, list[Permission]] = {
    RoleName.ADMINISTRATOR: list(Permission),  # all permissions
    RoleName.HR: [
        Permission.DASHBOARD_VIEW,
        Permission.EMPLOYEE_VIEW,
        Permission.EMPLOYEE_CREATE,
        Permission.EMPLOYEE_EDIT,
        Permission.EMPLOYEE_ARCHIVE,
        Permission.ATTENDANCE_VIEW,
        Permission.ATTENDANCE_CORRECT,
        Permission.ATTENDANCE_APPROVE,
        Permission.SCHEDULE_VIEW,
        Permission.SCHEDULE_CREATE,
        Permission.SCHEDULE_EDIT,
        Permission.LEAVE_VIEW,
        Permission.LEAVE_CREATE,
        Permission.LEAVE_APPROVE,
        Permission.OVERTIME_VIEW,
        Permission.OVERTIME_CREATE,
        Permission.OVERTIME_APPROVE,
        Permission.REPORTS_VIEW,
        Permission.REPORTS_EXPORT,
    ],
    RoleName.SUPERVISOR: [
        Permission.DASHBOARD_VIEW,
        Permission.ATTENDANCE_VIEW,
        Permission.LEAVE_VIEW,
        Permission.LEAVE_APPROVE,
        Permission.OVERTIME_VIEW,
        Permission.OVERTIME_APPROVE,
        Permission.REPORTS_VIEW,
    ],
    RoleName.KIOSK: [
        Permission.ATTENDANCE_KIOSK,
    ],
}

_PERMISSION_DESCRIPTIONS: dict[Permission, str] = {
    Permission.DASHBOARD_VIEW: "View dashboard",
    Permission.EMPLOYEE_VIEW: "View employees",
    Permission.EMPLOYEE_CREATE: "Create employees",
    Permission.EMPLOYEE_EDIT: "Edit employees",
    Permission.EMPLOYEE_ARCHIVE: "Archive employees",
    Permission.ATTENDANCE_VIEW: "View attendance records",
    Permission.ATTENDANCE_CORRECT: "Submit attendance corrections",
    Permission.ATTENDANCE_APPROVE: "Approve attendance corrections",
    Permission.ATTENDANCE_KIOSK: "Biometric kiosk attendance capture",
    Permission.BIOMETRIC_ENROLL: "Enroll biometrics",
    Permission.BIOMETRIC_MANAGE: "Manage biometric devices",
    Permission.SCHEDULE_VIEW: "View schedules",
    Permission.SCHEDULE_CREATE: "Create schedules",
    Permission.SCHEDULE_EDIT: "Edit schedules",
    Permission.LEAVE_VIEW: "View leave requests",
    Permission.LEAVE_CREATE: "Create leave requests",
    Permission.LEAVE_APPROVE: "Approve leave requests",
    Permission.OVERTIME_VIEW: "View overtime requests",
    Permission.OVERTIME_CREATE: "Create overtime requests",
    Permission.OVERTIME_APPROVE: "Approve overtime requests",
    Permission.REPORTS_VIEW: "View reports",
    Permission.REPORTS_EXPORT: "Export reports",
    Permission.USERS_MANAGE: "Manage system users",
    Permission.SETTINGS_MANAGE: "Manage system settings",
    Permission.AUDIT_VIEW: "View audit logs",
    Permission.BACKUP_MANAGE: "Manage database backup/restore",
}

_ROLE_DESCRIPTIONS: dict[RoleName, str] = {
    RoleName.ADMINISTRATOR: "Full system access",
    RoleName.HR: "HR staff — employees, attendance, schedules, leave, overtime, reports",
    RoleName.SUPERVISOR: "Team attendance, leave/overtime approval, team reports",
    RoleName.KIOSK: "Biometric attendance capture only",
}


def seed_roles_and_permissions(session: Session) -> None:
    """Idempotently create all roles and permissions.

    Safe to call multiple times — uses get-or-create logic.
    Does NOT create any user — that is handled by the setup wizard.
    """
    # 1. Ensure all permissions exist
    perm_models: dict[Permission, PermissionModel] = {}
    for perm in Permission:
        existing = session.query(PermissionModel).filter_by(name=perm.value).first()
        if existing is None:
            existing = PermissionModel(
                name=perm.value,
                description=_PERMISSION_DESCRIPTIONS.get(perm, ""),
            )
            session.add(existing)
            session.flush()
        perm_models[perm] = existing

    # 2. Ensure all roles exist with correct permission assignments
    for role_name in RoleName:
        role_model = session.query(RoleModel).filter_by(name=role_name.value).first()
        if role_model is None:
            role_model = RoleModel(
                name=role_name.value,
                description=_ROLE_DESCRIPTIONS.get(role_name, ""),
            )
            session.add(role_model)
            session.flush()

        # Assign permissions (idempotent — SQLAlchemy handles deduplication)
        assigned_perms = _ROLE_PERMISSION_MAP.get(role_name, [])
        role_model.permissions = [perm_models[p] for p in assigned_perms]

    session.flush()


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    positions: Mapped[list["PositionModel"]] = relationship(
        "PositionModel", back_populates="department", cascade="all, delete-orphan"
    )
    employees: Mapped[list["EmployeeModel"]] = relationship(
        "EmployeeModel", back_populates="department"
    )


class PositionModel(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="")
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    department: Mapped[Optional["DepartmentModel"]] = relationship(
        "DepartmentModel", back_populates="positions"
    )
    employees: Mapped[list["EmployeeModel"]] = relationship(
        "EmployeeModel", back_populates="position"
    )


class EmployeeModel(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Personal
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    suffix: Mapped[str] = mapped_column(String(20), default="")
    birth_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(20), default="")
    phone: Mapped[str] = mapped_column(String(50), default="")
    email: Mapped[str] = mapped_column(String(150), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    photo_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Employment
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("departments.id"), index=True)
    position_id: Mapped[Optional[int]] = mapped_column(ForeignKey("positions.id"))
    employment_type: Mapped[EmploymentType] = mapped_column(
        Enum(EmploymentType, values_callable=lambda x: [e.value for e in x]), default=EmploymentType.FULL_TIME
    )
    date_hired: Mapped[Optional[datetime.date]] = mapped_column(Date)
    status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus, values_callable=lambda x: [e.value for e in x]), default=EmploymentStatus.ACTIVE, index=True
    )
    supervisor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("employees.id"))

    # Attendance basics
    grace_period_mins: Mapped[int] = mapped_column(Integer, default=0)
    overtime_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    rest_day: Mapped[str] = mapped_column(String(20), default="Sunday")

    # Relationships
    department: Mapped[Optional["DepartmentModel"]] = relationship(
        "DepartmentModel", back_populates="employees"
    )
    position: Mapped[Optional["PositionModel"]] = relationship(
        "PositionModel", back_populates="employees"
    )
    supervisor: Mapped[Optional["EmployeeModel"]] = relationship(
        "EmployeeModel", remote_side=[id]
    )
    schedules: Mapped[list["EmployeeScheduleModel"]] = relationship(
        "EmployeeScheduleModel", back_populates="employee"
    )


class ShiftTemplateModel(Base):
    __tablename__ = "shift_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    break_start: Mapped[Optional[datetime.time]] = mapped_column(Time)
    break_end: Mapped[Optional[datetime.time]] = mapped_column(Time)
    grace_period_mins: Mapped[int] = mapped_column(Integer, default=0)
    late_threshold_mins: Mapped[int] = mapped_column(Integer, default=0)
    early_out_threshold_mins: Mapped[int] = mapped_column(Integer, default=0)
    overtime_threshold_mins: Mapped[int] = mapped_column(Integer, default=0)
    is_overnight: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    schedules: Mapped[list["EmployeeScheduleModel"]] = relationship(
        "EmployeeScheduleModel", back_populates="shift_template"
    )


class HolidayModel(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    holiday_type: Mapped[HolidayType] = mapped_column(
        Enum(HolidayType, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255))


class EmployeeScheduleModel(Base):
    __tablename__ = "employee_schedules"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_employee_schedule_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    shift_template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shift_templates.id"))
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)
    is_rest_day: Mapped[bool] = mapped_column(Boolean, default=False)
    schedule_status: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, values_callable=lambda x: [e.value for e in x]),
        default=ScheduleStatus.ACTIVE,
    )
    notes: Mapped[Optional[str]] = mapped_column(String(255))
    # Override times — nullable; UI to set them deferred to a later phase
    override_start_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    override_end_time: Mapped[Optional[datetime.time]] = mapped_column(Time)

    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel", back_populates="schedules")
    shift_template: Mapped[Optional["ShiftTemplateModel"]] = relationship(
        "ShiftTemplateModel", back_populates="schedules"
    )


# ── Attendance Models ─────────────────────────────────────────────────────────


class AttendanceEventModel(Base):
    """Raw, immutable biometric/manual scan record. Never overwrite."""
    __tablename__ = "attendance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_type: Mapped[AttendanceEventType] = mapped_column(
        Enum(AttendanceEventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False, index=True)
    biometric_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source: Mapped[AttendanceSource] = mapped_column(
        Enum(AttendanceSource, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AttendanceSource.MANUAL,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel")


class AttendanceRecordModel(Base):
    """Processed daily attendance result derived from raw events."""
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_attendance_record_employee_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    schedule_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("employee_schedules.id"), nullable=True
    )
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False, index=True)

    # Times stored as full DateTime (not just Time) to handle overnight correctly
    time_in: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    break_out: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    break_in: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    time_out: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    worked_minutes: Mapped[int] = mapped_column(Integer, default=0)
    late_minutes: Mapped[int] = mapped_column(Integer, default=0)
    undertime_minutes: Mapped[int] = mapped_column(Integer, default=0)
    overtime_minutes: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AttendanceStatus.INCOMPLETE,
        index=True,
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel")
    schedule: Mapped[Optional["EmployeeScheduleModel"]] = relationship("EmployeeScheduleModel")
    corrections: Mapped[list["AttendanceCorrectionModel"]] = relationship(
        "AttendanceCorrectionModel", back_populates="attendance_record", cascade="all, delete-orphan"
    )


class AttendanceCorrectionModel(Base):
    """Layered correction on top of an AttendanceRecord — original event is never overwritten."""
    __tablename__ = "attendance_corrections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attendance_record_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_records.id"), nullable=False, index=True
    )
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False, index=True)
    correction_type: Mapped[CorrectionType] = mapped_column(
        Enum(CorrectionType, values_callable=lambda x: [e.value for e in x]), nullable=False
    )
    original_value: Mapped[str] = mapped_column(String(255), nullable=False)
    requested_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    attachment_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[CorrectionStatus] = mapped_column(
        Enum(CorrectionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CorrectionStatus.PENDING,
        index=True,
    )
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    requested_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    reviewed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    attendance_record: Mapped["AttendanceRecordModel"] = relationship(
        "AttendanceRecordModel", back_populates="corrections"
    )
    employee: Mapped["EmployeeModel"] = relationship("EmployeeModel", foreign_keys=[employee_id])
    requester: Mapped["UserModel"] = relationship("UserModel", foreign_keys=[requested_by])
    reviewer: Mapped[Optional["UserModel"]] = relationship("UserModel", foreign_keys=[reviewed_by])

