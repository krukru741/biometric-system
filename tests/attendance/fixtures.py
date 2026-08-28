"""MockAttendanceEvent fixtures and factory helpers for Phase 4 test suite."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from biometric_attendance.core.enums.attendance import AttendanceEventType, AttendanceSource
from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType
from biometric_attendance.core.enums.scheduling import ScheduleStatus
from biometric_attendance.core.dtos.attendance_dtos import AttendanceEventEntity
from biometric_attendance.core.dtos.scheduling_dtos import ShiftTemplateEntity, EmployeeScheduleEntity
from biometric_attendance.core.dtos.workforce_dtos import EmployeeEntity

# ── Sentinel values ────────────────────────────────────────────────────────────

TODAY = dt.date(2026, 8, 28)
SHIFT_START = dt.time(8, 0)
SHIFT_END = dt.time(17, 0)
GRACE_MINS = 10
LATE_THRESHOLD_MINS = 0
EARLY_OUT_THRESHOLD_MINS = 0
OVERTIME_THRESHOLD_MINS = 30


# ── Factory helpers ────────────────────────────────────────────────────────────

def make_shift(
    *,
    start_time: dt.time = SHIFT_START,
    end_time: dt.time = SHIFT_END,
    grace_period_mins: int = GRACE_MINS,
    late_threshold_mins: int = LATE_THRESHOLD_MINS,
    early_out_threshold_mins: int = EARLY_OUT_THRESHOLD_MINS,
    overtime_threshold_mins: int = OVERTIME_THRESHOLD_MINS,
    break_start: Optional[dt.time] = None,
    break_end: Optional[dt.time] = None,
    is_overnight: bool = False,
    is_active: bool = True,
    id: int = 1,
    name: str = "Regular Shift",
) -> ShiftTemplateEntity:
    return ShiftTemplateEntity(
        id=id,
        name=name,
        start_time=start_time,
        end_time=end_time,
        break_start=break_start,
        break_end=break_end,
        grace_period_mins=grace_period_mins,
        late_threshold_mins=late_threshold_mins,
        early_out_threshold_mins=early_out_threshold_mins,
        overtime_threshold_mins=overtime_threshold_mins,
        is_overnight=is_overnight,
        is_active=is_active,
    )


def make_employee(
    *,
    id: int = 1,
    employee_id: str = "EMP-001",
    first_name: str = "Test",
    last_name: str = "Employee",
    grace_period_mins: int = GRACE_MINS,
    overtime_eligible: bool = True,
    rest_day: str = "Sunday",
    status: EmploymentStatus = EmploymentStatus.ACTIVE,
) -> EmployeeEntity:
    return EmployeeEntity(
        id=id,
        employee_id=employee_id,
        first_name=first_name,
        middle_name="",
        last_name=last_name,
        suffix="",
        birth_date=None,
        gender="",
        phone="",
        email="",
        address="",
        photo_path=None,
        department_id=None,
        department_name=None,
        position_id=None,
        position_name=None,
        employment_type=EmploymentType.FULL_TIME,
        date_hired=None,
        status=status,
        supervisor_id=None,
        grace_period_mins=grace_period_mins,
        overtime_eligible=overtime_eligible,
        rest_day=rest_day,
    )


def make_schedule(
    *,
    id: int = 1,
    employee_id: int = 1,
    shift_id: int = 1,
    date: dt.date = TODAY,
    is_rest_day: bool = False,
    notes: Optional[str] = None,
) -> EmployeeScheduleEntity:
    return EmployeeScheduleEntity(
        id=id,
        employee_id=employee_id,
        employee_id_str="EMP-001",
        employee_name="Test Employee",
        shift_template_id=shift_id,
        shift_name="Regular Shift",
        date=date,
        is_rest_day=is_rest_day,
        schedule_status=ScheduleStatus.ACTIVE,
        notes=notes,
        override_start_time=None,
        override_end_time=None,
    )


@dataclass
class MockAttendanceEvent:
    """Lightweight mock event used to feed the processor in tests."""
    employee_id: int
    event_type: AttendanceEventType
    timestamp: dt.datetime
    device_id: str = "MOCK-01"
    biometric_verified: bool = True
    source: AttendanceSource = AttendanceSource.MOCK
    id: int = 1
    employee_id_str: str = "EMP-001"
    employee_name: str = "Test Employee"

    def to_entity(self) -> AttendanceEventEntity:
        return AttendanceEventEntity(
            id=self.id,
            employee_id=self.employee_id,
            employee_id_str=self.employee_id_str,
            employee_name=self.employee_name,
            device_id=self.device_id,
            event_type=self.event_type,
            timestamp=self.timestamp,
            biometric_verified=self.biometric_verified,
            source=self.source,
            created_at=dt.datetime.now(),
        )


# ── Timestamp helpers ──────────────────────────────────────────────────────────

def ts(date: dt.date, h: int, m: int = 0) -> dt.datetime:
    """Build a datetime from a date + hour/minute."""
    return dt.datetime(date.year, date.month, date.day, h, m)
