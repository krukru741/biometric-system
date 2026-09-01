"""AttendanceProcessor — full event → record pipeline orchestrator.

Processing flow (per 13-ATTENDANCE-ENGINE.md §3):
  1.  Duplicate check (same employee, same event_type, within 60s)
  2.  Identify employee
  3.  Resolve schedule → ScheduleResolver (handles overnight routing)
  4.  Check Holiday
  5.  Check Rest Day
  6.  [STUB] Check Approved Leave (always returns False; Phase 6 will implement)
  7.  Merge event into AttendanceRecord (get_or_create, overnight-aware)
  8.  If IN only → status = INCOMPLETE
  9.  If IN + OUT → AttendanceCalculationService → assign status
  10. Save AttendanceRecord
  11. Return ProcessEventResult
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from biometric_attendance.core.dtos.attendance_dtos import (
    AttendanceEventEntity,
    AttendanceRecordEntity,
    ProcessEventResult,
)
from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    AttendanceStatus,
)
from biometric_attendance.core.interfaces.i_attendance_interfaces import (
    IAttendanceCalculationService,
    IAttendanceProcessor,
    IScheduleResolver,
)
from biometric_attendance.infrastructure.repositories.attendance_repository import (
    AttendanceEventRepository,
    AttendanceRecordRepository,
)
from biometric_attendance.infrastructure.repositories.workforce_repository import EmployeeRepository

# Within this many seconds, a second event of the same type is a duplicate
_DUPLICATE_WINDOW_SECONDS = 60


class AttendanceProcessor(IAttendanceProcessor):

    def __init__(
        self,
        event_repository: AttendanceEventRepository,
        record_repository: AttendanceRecordRepository,
        employee_repository: EmployeeRepository,
        schedule_resolver: IScheduleResolver,
        calculation_service: IAttendanceCalculationService,
    ) -> None:
        self._events = event_repository
        self._records = record_repository
        self._employees = employee_repository
        self._resolver = schedule_resolver
        self._calc = calculation_service

    # ── Leave stub ─────────────────────────────────────────────────────────────

    def _has_approved_leave(self, employee_id: int, date: dt.date) -> bool:
        """Phase 6 stub — always returns False.

        Replace this with a real LeaveService lookup in Phase 6.
        The processor's interface is intentionally designed to accept this
        without any further changes.
        """
        return False

    # ── Main pipeline ──────────────────────────────────────────────────────────

    def process_event(self, event: AttendanceEventEntity) -> ProcessEventResult:
        from biometric_attendance.infrastructure.data.database import auto_session
        base_session = getattr(self._events, "_session", None)

        with auto_session(base_session) as session:
            local_events = AttendanceEventRepository(session)
            local_records = AttendanceRecordRepository(session)
            local_employees = EmployeeRepository(session)

            employee_id = event.employee_id
            event_ts = event.timestamp
            event_date = event_ts.date()

            # 1. Duplicate detection: same employee + same event_type within 60 s
            since = event_ts - dt.timedelta(seconds=_DUPLICATE_WINDOW_SECONDS)
            recent = local_events.get_recent_events(employee_id=employee_id, since=since)
            for r in recent:
                if r.id != event.id and r.event_type == event.event_type:
                    # Build a minimal placeholder record entity for the response
                    existing_record = local_records.get_by_employee_and_date(employee_id, event_date)
                    if existing_record is None:
                        # Even if no record yet, return a meaningful response
                        existing_record = AttendanceRecordEntity(
                            id=0, employee_id=employee_id, employee_id_str=event.employee_id_str, employee_name=event.employee_name,
                            schedule_id=None, date=event_date,
                            time_in=None, break_out=None, break_in=None, time_out=None,
                            worked_minutes=0, late_minutes=0, undertime_minutes=0, overtime_minutes=0,
                            status=AttendanceStatus.INCOMPLETE,
                            created_at=dt.datetime.now(), updated_at=dt.datetime.now(),
                        )
                    dup_time = r.timestamp.strftime("%H:%M:%S")
                    return ProcessEventResult(
                        record=existing_record,
                        is_new_record=False,
                        message=f"Duplicate scan ignored — already recorded at {dup_time}",
                        is_duplicate=True,
                    )

            # 2. Fetch employee (needed for rest_day default and overtime_eligible)
            all_employees = local_employees.get_all()
            employee = next((e for e in all_employees if e.id == employee_id), None)
            if employee is None:
                raise ValueError(f"Employee with id={employee_id} not found.")

            # 3. Resolve schedule (handles overnight: checks prev day if needed)
            schedule = self._resolver.resolve(employee_id, event_date)
            shift = self._resolver.get_shift(schedule) if schedule else None

            # 4. Holiday check
            holiday = self._resolver.get_holiday(event_date)

            # 5. Rest day check
            is_rest = self._resolver.is_rest_day(employee, event_date)

            # 6. Leave check (stub)
            is_on_leave = self._has_approved_leave(employee_id, event_date)

            # 7. Get or create AttendanceRecord (overnight-aware)
            schedule_id = schedule.id if schedule else None
            record_model, is_new = local_records.get_or_create_for_date(
                employee_id=employee_id,
                date=event_date,
                schedule_id=schedule_id,
            )

            # Merge the event into the record
            if event.event_type == AttendanceEventType.IN:
                if record_model.time_in is None:
                    record_model.time_in = event_ts
            elif event.event_type == AttendanceEventType.OUT:
                record_model.time_out = event_ts
            elif event.event_type == AttendanceEventType.BREAK_OUT:
                record_model.break_out = event_ts
            elif event.event_type == AttendanceEventType.BREAK_IN:
                record_model.break_in = event_ts

            # 8-9. Assign status per canonical priority order
            if holiday is not None:
                record_model.status = AttendanceStatus.HOLIDAY
            elif is_rest:
                record_model.status = AttendanceStatus.REST_DAY
            elif is_on_leave:
                record_model.status = AttendanceStatus.ON_LEAVE
            elif record_model.time_in is not None and record_model.time_out is None:
                record_model.status = AttendanceStatus.INCOMPLETE
            elif record_model.time_in is not None and record_model.time_out is not None:
                if shift is not None:
                    # Determine which date to pass to calculation service:
                    # Use the record's own date (= IN date per Q2)
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
                else:
                    # No shift template — can still mark PRESENT if both times exist
                    gross = int((record_model.time_out - record_model.time_in).total_seconds() / 60)
                    record_model.worked_minutes = max(0, gross)
                    record_model.status = AttendanceStatus.PRESENT

            # 10. Save
            entity = local_records.save_model(record_model)

            # 11. Return
            return ProcessEventResult(
                record=entity,
                is_new_record=is_new,
                message=f"Event {event.event_type.value} processed — status: {entity.status.value}",
                is_duplicate=False,
            )
