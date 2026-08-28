"""Abstract interfaces for the Attendance Engine.

All concrete implementations in application/attendance/ must inherit
from these ABCs. This allows Phase 5 to swap the event source
(biometric device → real adapter) without touching engine logic.
"""
from __future__ import annotations

import datetime as dt
from abc import ABC, abstractmethod
from typing import Optional

from biometric_attendance.core.dtos.attendance_dtos import (
    AttendanceCorrectionEntity,
    AttendanceEventEntity,
    AttendanceRecordEntity,
    CalculationResult,
    ProcessEventResult,
)
from biometric_attendance.core.dtos.scheduling_dtos import (
    EmployeeScheduleEntity,
    HolidayEntity,
    ShiftTemplateEntity,
)
from biometric_attendance.core.dtos.workforce_dtos import EmployeeEntity
from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    AttendanceSource,
    CorrectionType,
)


class IScheduleResolver(ABC):
    """Resolves schedule, shift, holiday, and rest-day information for a date."""

    @abstractmethod
    def resolve(self, employee_id: int, date: dt.date) -> Optional[EmployeeScheduleEntity]:
        """Return the EmployeeScheduleEntity for employee on date.
        
        Handles overnight: if no record exists for `date`, checks whether the
        employee has an open overnight record starting on `date - 1 day`.
        """

    @abstractmethod
    def get_shift(self, schedule: EmployeeScheduleEntity) -> Optional[ShiftTemplateEntity]:
        """Return the ShiftTemplateEntity for the given schedule."""

    @abstractmethod
    def get_holiday(self, date: dt.date) -> Optional[HolidayEntity]:
        """Return HolidayEntity if `date` is a holiday, else None."""

    @abstractmethod
    def is_rest_day(self, employee: EmployeeEntity, date: dt.date) -> bool:
        """Return True if `date` is a rest day for the employee."""


class IAttendanceCalculationService(ABC):
    """Pure calculation — no DB access, no side effects.
    
    Status priority order (highest → lowest):
        HOLIDAY > REST_DAY > ON_LEAVE > INCOMPLETE > HALF_DAY
        > LATE > UNDERTIME > OVERTIME > PRESENT
    """

    @abstractmethod
    def calculate(
        self,
        time_in: dt.datetime,
        time_out: Optional[dt.datetime],
        break_out: Optional[dt.datetime],
        break_in: Optional[dt.datetime],
        shift: ShiftTemplateEntity,
        schedule_date: dt.date,
        overtime_eligible: bool,
    ) -> CalculationResult:
        """Compute worked/late/undertime/overtime minutes and final status."""


class IAttendanceProcessor(ABC):
    """Orchestrates the full event → record pipeline."""

    @abstractmethod
    def process_event(self, event: AttendanceEventEntity) -> ProcessEventResult:
        """Process a single attendance event and return the updated record."""


class IAttendanceEventService(ABC):
    """High-level service for recording and retrieving raw events."""

    @abstractmethod
    def record_event(
        self,
        employee_id: int,
        event_type: AttendanceEventType,
        timestamp: dt.datetime,
        device_id: Optional[str] = None,
        biometric_verified: bool = False,
        source: AttendanceSource = AttendanceSource.MANUAL,
    ) -> ProcessEventResult:
        """Save a raw event and trigger the processor. Returns the result."""

    @abstractmethod
    def get_events(
        self,
        employee_id: int,
        date: dt.date,
    ) -> list[AttendanceEventEntity]:
        """Return all raw events for an employee on a date, sorted by timestamp."""


class IAttendanceCorrectionService(ABC):
    """Manages the correction request → approval workflow."""

    @abstractmethod
    def submit_correction(
        self,
        record_id: int,
        employee_id: int,
        correction_type: CorrectionType,
        original_value: str,
        requested_value: str,
        reason: str,
        requested_by_id: int,
        attachment_path: Optional[str] = None,
    ) -> AttendanceCorrectionEntity:
        """Create a PENDING correction request."""

    @abstractmethod
    def approve_correction(
        self,
        correction_id: int,
        reviewer_user_id: int,
    ) -> AttendanceCorrectionEntity:
        """Approve the correction and re-calculate the attendance record."""

    @abstractmethod
    def reject_correction(
        self,
        correction_id: int,
        reviewer_user_id: int,
        comment: str,
    ) -> AttendanceCorrectionEntity:
        """Reject the correction; original record is unchanged."""

    @abstractmethod
    def get_pending_corrections(self) -> list[AttendanceCorrectionEntity]:
        """Return all corrections with status=PENDING."""
