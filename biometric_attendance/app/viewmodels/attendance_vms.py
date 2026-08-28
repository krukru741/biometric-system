"""ViewModels for the Attendance module."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot

from biometric_attendance.core.dtos.attendance_dtos import (
    AttendanceCorrectionEntity,
    AttendanceEventEntity,
    AttendanceRecordEntity,
    ProcessEventResult,
)
from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    AttendanceSource,
    CorrectionType,
)
from biometric_attendance.application.attendance.event_service import AttendanceEventService
from biometric_attendance.application.attendance.correction_service import AttendanceCorrectionService
from biometric_attendance.infrastructure.repositories.attendance_repository import (
    AttendanceRecordRepository,
    AttendanceEventRepository,
)
from biometric_attendance.infrastructure.repositories.workforce_repository import EmployeeRepository


class AttendanceLiveViewModel(QObject):
    """ViewModel for the Live Attendance scan simulator panel."""

    event_processed = Signal(object)       # ProcessEventResult
    events_loaded = Signal(list)           # list[AttendanceEventEntity]
    employees_loaded = Signal(list)        # list[EmployeeEntity]
    error_occurred = Signal(str)

    def __init__(
        self,
        event_service: AttendanceEventService,
        employee_repository: EmployeeRepository,
    ) -> None:
        super().__init__()
        self._service = event_service
        self._employees = employee_repository

    def load_employees(self) -> None:
        try:
            self.employees_loaded.emit(self._employees.get_all())
        except Exception as e:
            self.error_occurred.emit(str(e))

    def submit_scan(
        self,
        employee_id: int,
        event_type: AttendanceEventType,
        timestamp: dt.datetime,
        device_id: Optional[str] = None,
    ) -> None:
        try:
            result = self._service.record_event(
                employee_id=employee_id,
                event_type=event_type,
                timestamp=timestamp,
                device_id=device_id,
                biometric_verified=False,
                source=AttendanceSource.MOCK,
            )
            self.event_processed.emit(result)
            # Refresh today's event log
            self.load_recent_events(employee_id, timestamp.date())
        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_recent_events(self, employee_id: int, date: dt.date) -> None:
        try:
            events = self._service.get_events(employee_id=employee_id, date=date)
            self.events_loaded.emit(events)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AttendanceRecordsViewModel(QObject):
    """ViewModel for the Attendance Records table view."""

    records_loaded = Signal(list)          # list[AttendanceRecordEntity]
    employees_loaded = Signal(list)
    absent_generated = Signal(int)         # count of ABSENT records created
    error_occurred = Signal(str)

    def __init__(
        self,
        record_repository: AttendanceRecordRepository,
        employee_repository: EmployeeRepository,
    ) -> None:
        super().__init__()
        self._records = record_repository
        self._employees = employee_repository

    def load_employees(self) -> None:
        try:
            self.employees_loaded.emit(self._employees.get_all())
        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_records(
        self,
        start_date: dt.date,
        end_date: dt.date,
        employee_id: Optional[int] = None,
    ) -> None:
        try:
            records = self._records.get_by_date_range(
                start_date=start_date, end_date=end_date, employee_id=employee_id
            )
            self.records_loaded.emit(records)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def generate_absent_records(self, date: dt.date) -> None:
        """Create ABSENT records for employees with no attendance on the given date.

        Only creates records for Active employees who have a schedule on that date
        and no existing attendance record. Per Q3, this is manual-trigger only.
        """
        try:
            all_employees = self._employees.get_all()
            from biometric_attendance.core.enums.workforce import EmploymentStatus
            active_ids = [e.id for e in all_employees if e.status == EmploymentStatus.ACTIVE]
            count = self._records.create_absent_records(date=date, employee_ids=active_ids)
            self.absent_generated.emit(count)
            self.load_records(start_date=date, end_date=date)
        except Exception as e:
            self.error_occurred.emit(str(e))


class AttendanceCorrectionsViewModel(QObject):
    """ViewModel for the Corrections approval workflow."""

    pending_loaded = Signal(list)          # list[AttendanceCorrectionEntity]
    my_corrections_loaded = Signal(list)
    correction_submitted = Signal(object)
    correction_approved = Signal(object)
    correction_rejected = Signal(object)
    employees_loaded = Signal(list)
    error_occurred = Signal(str)

    def __init__(
        self,
        correction_service: AttendanceCorrectionService,
        employee_repository: EmployeeRepository,
        record_repository: AttendanceRecordRepository,
    ) -> None:
        super().__init__()
        self._service = correction_service
        self._employees = employee_repository
        self._records = record_repository

    def load_employees(self) -> None:
        try:
            self.employees_loaded.emit(self._employees.get_all())
        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_pending(self) -> None:
        try:
            self.pending_loaded.emit(self._service.get_pending_corrections())
        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_my_corrections(self, employee_id: int) -> None:
        try:
            self.my_corrections_loaded.emit(
                self._service._corrections.get_by_employee(employee_id)
            )
        except Exception as e:
            self.error_occurred.emit(str(e))

    def submit_correction(
        self,
        record_id: int,
        employee_id: int,
        correction_type: CorrectionType,
        original_value: str,
        requested_value: str,
        reason: str,
        requested_by_id: int,
    ) -> None:
        try:
            result = self._service.submit_correction(
                record_id=record_id,
                employee_id=employee_id,
                correction_type=correction_type,
                original_value=original_value,
                requested_value=requested_value,
                reason=reason,
                requested_by_id=requested_by_id,
            )
            self.correction_submitted.emit(result)
            self.load_pending()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def approve_correction(self, correction_id: int, reviewer_id: int) -> None:
        try:
            result = self._service.approve_correction(correction_id, reviewer_id)
            self.correction_approved.emit(result)
            self.load_pending()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def reject_correction(
        self, correction_id: int, reviewer_id: int, comment: str
    ) -> None:
        try:
            result = self._service.reject_correction(correction_id, reviewer_id, comment)
            self.correction_rejected.emit(result)
            self.load_pending()
        except Exception as e:
            self.error_occurred.emit(str(e))
