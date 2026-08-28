"""AttendanceCalculationService — pure calculation, no DB access.

Canonical status priority order (highest → lowest):
    HOLIDAY > REST_DAY > ON_LEAVE > INCOMPLETE > HALF_DAY
    > LATE > UNDERTIME > OVERTIME > PRESENT

Context-level statuses (HOLIDAY, REST_DAY, ON_LEAVE, INCOMPLETE) are
decided by AttendanceProcessor *before* calling this service.
This service handles the time-math statuses:
    HALF_DAY, LATE, UNDERTIME, OVERTIME, PRESENT.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from biometric_attendance.core.dtos.attendance_dtos import CalculationResult
from biometric_attendance.core.dtos.scheduling_dtos import ShiftTemplateEntity
from biometric_attendance.core.enums.attendance import AttendanceStatus
from biometric_attendance.core.interfaces.i_attendance_interfaces import IAttendanceCalculationService


# Priority order reference (index 0 = highest priority among time-math statuses)
# Context statuses handled upstream: HOLIDAY, REST_DAY, ON_LEAVE, INCOMPLETE
_TIME_MATH_PRIORITY = [
    AttendanceStatus.HALF_DAY,
    AttendanceStatus.LATE,
    AttendanceStatus.UNDERTIME,
    AttendanceStatus.OVERTIME,
    AttendanceStatus.PRESENT,
]


class AttendanceCalculationService(IAttendanceCalculationService):
    """Pure calculation — no DB access, no side effects.

    All calculations are based on DateTime objects so that overnight shifts
    crossing midnight are handled correctly.
    """

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
        """Compute attended-time metrics and assign the canonical status.

        Args:
            time_in: Actual clock-in datetime.
            time_out: Actual clock-out datetime (None → INCOMPLETE, handled upstream).
            break_out/break_in: Break datetimes (both None → no break).
            shift: The ShiftTemplateEntity defining expected hours.
            schedule_date: The attendance record date (IN date, per Q2).
            overtime_eligible: Whether this employee can earn overtime.

        Returns:
            CalculationResult with all minute-based fields and the final status.
        """
        if time_out is None:
            # Caller should not reach here; return safe zero-state
            return CalculationResult(
                worked_minutes=0,
                late_minutes=0,
                undertime_minutes=0,
                overtime_minutes=0,
                status=AttendanceStatus.INCOMPLETE,
            )

        # ── Build shift boundaries as full DateTime objects ────────────────────
        shift_start = dt.datetime.combine(schedule_date, shift.start_time)
        if shift.is_overnight:
            shift_end = dt.datetime.combine(schedule_date + dt.timedelta(days=1), shift.end_time)
        else:
            shift_end = dt.datetime.combine(schedule_date, shift.end_time)

        # Expected work duration (shift minus any scheduled break)
        expected_minutes = int((shift_end - shift_start).total_seconds() / 60)
        if shift.break_start and shift.break_end:
            break_sched_start = dt.datetime.combine(schedule_date, shift.break_start)
            break_sched_end = dt.datetime.combine(schedule_date, shift.break_end)
            scheduled_break_mins = int((break_sched_end - break_sched_start).total_seconds() / 60)
            expected_minutes -= max(0, scheduled_break_mins)

        # ── Late calculation ───────────────────────────────────────────────────
        grace_delta = dt.timedelta(minutes=shift.grace_period_mins)
        latest_on_time = shift_start + grace_delta
        if time_in <= latest_on_time:
            late_minutes = 0
        else:
            # Late = actual time_in minus shift_start (not minus grace)
            late_minutes = int((time_in - shift_start).total_seconds() / 60)
            late_minutes = max(0, late_minutes)

        # ── Worked minutes ─────────────────────────────────────────────────────
        gross_minutes = int((time_out - time_in).total_seconds() / 60)

        # Deduct actual break duration if both break timestamps exist
        actual_break_mins = 0
        if break_out and break_in and break_in > break_out:
            actual_break_mins = int((break_in - break_out).total_seconds() / 60)

        worked_minutes = max(0, gross_minutes - actual_break_mins)

        # ── Half-day check (< 50% of expected shift) ──────────────────────────
        half_day_threshold = expected_minutes // 2
        is_half_day = 0 < worked_minutes < half_day_threshold

        # ── Undertime ─────────────────────────────────────────────────────────
        early_out_threshold = dt.timedelta(minutes=shift.early_out_threshold_mins)
        if time_out < (shift_end - early_out_threshold):
            undertime_minutes = max(0, expected_minutes - worked_minutes)
        else:
            undertime_minutes = 0

        # ── Overtime ──────────────────────────────────────────────────────────
        if overtime_eligible:
            ot_threshold = dt.timedelta(minutes=shift.overtime_threshold_mins)
            if time_out > (shift_end + ot_threshold):
                overtime_minutes = max(0, worked_minutes - expected_minutes)
            else:
                overtime_minutes = 0
        else:
            overtime_minutes = 0

        # ── Status assignment (priority order) ────────────────────────────────
        # Full priority (context statuses already filtered upstream):
        #   HOLIDAY > REST_DAY > ON_LEAVE > INCOMPLETE
        #   > HALF_DAY > LATE > UNDERTIME > OVERTIME > PRESENT
        if is_half_day:
            status = AttendanceStatus.HALF_DAY
        elif late_minutes > 0:
            status = AttendanceStatus.LATE
        elif undertime_minutes > 0:
            status = AttendanceStatus.UNDERTIME
        elif overtime_minutes > 0:
            status = AttendanceStatus.OVERTIME
        else:
            status = AttendanceStatus.PRESENT

        return CalculationResult(
            worked_minutes=worked_minutes,
            late_minutes=late_minutes,
            undertime_minutes=undertime_minutes,
            overtime_minutes=overtime_minutes,
            status=status,
        )
