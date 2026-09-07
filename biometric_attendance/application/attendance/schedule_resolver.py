"""ScheduleResolver — resolves schedule, shift, holiday, and rest-day for a date.

Resolves exact calendar dates; AttendanceProcessor routes overnight events
to the date of their open record before requesting schedule context.
"""
from __future__ import annotations

import datetime as dt
from typing import Optional

from biometric_attendance.core.dtos.scheduling_dtos import (
    EmployeeScheduleEntity,
    HolidayEntity,
    ShiftTemplateEntity,
)
from biometric_attendance.core.dtos.workforce_dtos import EmployeeEntity
from biometric_attendance.core.interfaces.i_attendance_interfaces import IScheduleResolver
from biometric_attendance.infrastructure.repositories.scheduling_repository import (
    EmployeeScheduleRepository,
    HolidayRepository,
    ShiftTemplateRepository,
)


class ScheduleResolver(IScheduleResolver):
    def __init__(
        self,
        schedule_repository: EmployeeScheduleRepository,
        shift_repository: ShiftTemplateRepository,
        holiday_repository: HolidayRepository,
    ) -> None:
        self._schedules = schedule_repository
        self._shifts = shift_repository
        self._holidays = holiday_repository

    def resolve(self, employee_id: int, date: dt.date) -> Optional[EmployeeScheduleEntity]:
        """Return the schedule for this exact calendar date."""
        schedules = self._schedules.get_schedules(employee_id=employee_id, start_date=date, end_date=date)
        if schedules:
            return schedules[0]

        return None

    def get_shift(self, schedule: EmployeeScheduleEntity) -> Optional[ShiftTemplateEntity]:
        if schedule.shift_template_id is None:
            return None
        all_shifts = self._shifts.get_all()
        for s in all_shifts:
            if s.id == schedule.shift_template_id:
                return s
        return None

    def get_holiday(self, date: dt.date) -> Optional[HolidayEntity]:
        holidays = self._holidays.get_by_year(date.year)
        for h in holidays:
            if h.date == date:
                return h
        return None

    def is_rest_day(self, employee: EmployeeEntity, date: dt.date) -> bool:
        """Return True if `date` is a rest day for this employee.

        Checks the explicit schedule rest-day flag first; falls back to
        the employee's configured default rest_day (weekday name).
        """
        schedules = self._schedules.get_schedules(
            employee_id=employee.id, start_date=date, end_date=date
        )
        if schedules:
            return schedules[0].is_rest_day

        # Fall back to employee's default rest day setting
        _WEEKDAY_NAMES = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]
        return _WEEKDAY_NAMES[date.weekday()] == (employee.rest_day or "Sunday")
