"""DTOs for the Attendance domain."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Optional

from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    AttendanceSource,
    AttendanceStatus,
    CorrectionStatus,
    CorrectionType,
)


@dataclass(frozen=True)
class AttendanceEventEntity:
    id: int
    employee_id: int
    employee_id_str: str
    employee_name: str
    device_id: Optional[str]
    event_type: AttendanceEventType
    timestamp: dt.datetime
    biometric_verified: bool
    source: AttendanceSource
    created_at: dt.datetime


@dataclass(frozen=True)
class AttendanceRecordEntity:
    id: int
    employee_id: int
    employee_id_str: str
    employee_name: str
    schedule_id: Optional[int]
    date: dt.date
    time_in: Optional[dt.datetime]
    break_out: Optional[dt.datetime]
    break_in: Optional[dt.datetime]
    time_out: Optional[dt.datetime]
    worked_minutes: int
    late_minutes: int
    undertime_minutes: int
    overtime_minutes: int
    status: AttendanceStatus
    created_at: dt.datetime
    updated_at: dt.datetime

    @property
    def worked_display(self) -> str:
        h, m = divmod(self.worked_minutes, 60)
        return f"{h}h {m:02d}m"


@dataclass(frozen=True)
class AttendanceCorrectionEntity:
    id: int
    attendance_record_id: int
    employee_id: int
    employee_id_str: str
    employee_name: str
    correction_type: CorrectionType
    original_value: str
    requested_value: str
    reason: str
    attachment_path: Optional[str]
    status: CorrectionStatus
    requested_by: int
    requested_at: dt.datetime
    reviewed_by: Optional[int]
    reviewed_at: Optional[dt.datetime]
    review_comment: Optional[str]
    created_at: dt.datetime
    updated_at: dt.datetime


@dataclass(frozen=True)
class CalculationResult:
    """Pure output from AttendanceCalculationService."""
    worked_minutes: int
    late_minutes: int
    undertime_minutes: int
    overtime_minutes: int
    status: AttendanceStatus


@dataclass(frozen=True)
class ProcessEventResult:
    """Return value from AttendanceProcessor.process_event."""
    record: AttendanceRecordEntity
    is_new_record: bool
    # Human-readable message for the UI (e.g. duplicate feedback)
    message: str
    # True if the event was a no-op duplicate
    is_duplicate: bool = False
