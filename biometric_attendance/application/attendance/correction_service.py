"""AttendanceCorrectionService — manages correction request → approval workflow.

Traceability chain (per 06-ATTENDANCE.md §7.2):
    AttendanceEvent → AttendanceRecord → AttendanceCorrection → AuditLog

Original biometric events are never modified. Corrections apply on top.
When approved, the record is fully recalculated using the corrected values.
"""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from biometric_attendance.core.dtos.attendance_dtos import AttendanceCorrectionEntity
from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    CorrectionStatus,
    CorrectionType,
)
from biometric_attendance.core.interfaces.i_attendance_interfaces import (
    IAttendanceCorrectionService,
    IAttendanceCalculationService,
    IScheduleResolver,
)
from biometric_attendance.infrastructure.repositories.attendance_repository import (
    AttendanceCorrectionRepository,
    AttendanceRecordRepository,
)
from biometric_attendance.infrastructure.repositories.workforce_repository import EmployeeRepository
from biometric_attendance.infrastructure.data.models import AttendanceRecordModel


class AttendanceCorrectionService(IAttendanceCorrectionService):
    def __init__(
        self,
        correction_repository: AttendanceCorrectionRepository,
        record_repository: AttendanceRecordRepository,
        employee_repository: EmployeeRepository,
        schedule_resolver: IScheduleResolver,
        calculation_service: IAttendanceCalculationService,
    ) -> None:
        self._corrections = correction_repository
        self._records = record_repository
        self._employees = employee_repository
        self._resolver = schedule_resolver
        self._calc = calculation_service

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
        return self._corrections.create(
            attendance_record_id=record_id,
            employee_id=employee_id,
            correction_type=correction_type,
            original_value=original_value,
            requested_value=requested_value,
            reason=reason,
            attachment_path=attachment_path,
            status=CorrectionStatus.PENDING,
            requested_by=requested_by_id,
            requested_at=dt.datetime.now(),
        )

    def approve_correction(
        self,
        correction_id: int,
        reviewer_user_id: int,
    ) -> AttendanceCorrectionEntity:
        """Approve and re-run full calculation on the corrected record."""
        correction_entity = self._corrections.get_by_record(
            record_id=0  # placeholder — we'll fetch directly
        )
        # Fetch the correction model directly
        from biometric_attendance.infrastructure.data.models import AttendanceCorrectionModel
        session = self._corrections._session
        correction_model = session.query(AttendanceCorrectionModel).filter_by(id=correction_id).first()
        if correction_model is None:
            raise ValueError(f"Correction {correction_id} not found.")

        record_model = session.query(AttendanceRecordModel).filter_by(
            id=correction_model.attendance_record_id
        ).first()
        if record_model is None:
            raise ValueError(f"Record {correction_model.attendance_record_id} not found.")

        # Apply the correction to the record
        ctype = correction_model.correction_type
        new_val_str = correction_model.requested_value

        def _parse_dt(s: str) -> Optional[dt.datetime]:
            try:
                return dt.datetime.fromisoformat(s)
            except Exception:
                return None

        if ctype == CorrectionType.TIME_IN:
            record_model.time_in = _parse_dt(new_val_str)
        elif ctype == CorrectionType.TIME_OUT:
            record_model.time_out = _parse_dt(new_val_str)
        elif ctype == CorrectionType.BREAK_OUT:
            record_model.break_out = _parse_dt(new_val_str)
        elif ctype == CorrectionType.BREAK_IN:
            record_model.break_in = _parse_dt(new_val_str)
        elif ctype == CorrectionType.STATUS:
            from biometric_attendance.core.enums.attendance import AttendanceStatus
            try:
                record_model.status = AttendanceStatus(new_val_str)
            except ValueError:
                pass

        # Full recalculation when both times exist
        if record_model.time_in and record_model.time_out:
            all_employees = self._employees.get_all()
            employee = next((e for e in all_employees if e.id == record_model.employee_id), None)
            schedule = self._resolver.resolve(record_model.employee_id, record_model.date)
            shift = self._resolver.get_shift(schedule) if schedule else None
            if shift and employee:
                calc = self._calc.calculate(
                    time_in=record_model.time_in,
                    time_out=record_model.time_out,
                    break_out=record_model.break_out,
                    break_in=record_model.break_in,
                    shift=shift,
                    schedule_date=record_model.date,
                    overtime_eligible=employee.overtime_eligible,
                )
                record_model.worked_minutes = calc.worked_minutes
                record_model.late_minutes = calc.late_minutes
                record_model.undertime_minutes = calc.undertime_minutes
                record_model.overtime_minutes = calc.overtime_minutes
                record_model.status = calc.status

        session.commit()

        return self._corrections.update_status(
            correction_id=correction_id,
            status=CorrectionStatus.APPROVED,
            reviewer_id=reviewer_user_id,
            reviewed_at=dt.datetime.now(),
        )

    def reject_correction(
        self,
        correction_id: int,
        reviewer_user_id: int,
        comment: str,
    ) -> AttendanceCorrectionEntity:
        return self._corrections.update_status(
            correction_id=correction_id,
            status=CorrectionStatus.REJECTED,
            reviewer_id=reviewer_user_id,
            reviewed_at=dt.datetime.now(),
            comment=comment,
        )

    def get_pending_corrections(self) -> List[AttendanceCorrectionEntity]:
        return self._corrections.get_pending()
