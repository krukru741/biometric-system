"""DTOs for the Scheduling domain (ShiftTemplates, Holidays, EmployeeSchedules)."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from biometric_attendance.core.enums.scheduling import HolidayType, ScheduleStatus


@dataclass(frozen=True)
class ShiftTemplateEntity:
    id: int
    name: str
    start_time: dt.time
    end_time: dt.time
    break_start: Optional[dt.time]
    break_end: Optional[dt.time]
    grace_period_mins: int
    late_threshold_mins: int
    early_out_threshold_mins: int
    overtime_threshold_mins: int
    is_overnight: bool
    is_active: bool

    @property
    def duration_hours(self) -> float:
        """Approximate shift duration, accounting for overnight."""
        start_mins = self.start_time.hour * 60 + self.start_time.minute
        end_mins = self.end_time.hour * 60 + self.end_time.minute
        if self.is_overnight:
            end_mins += 24 * 60
        total = end_mins - start_mins
        return round(total / 60, 2)

    @property
    def display_time(self) -> str:
        fmt = "%I:%M %p"
        label = f"{self.start_time.strftime(fmt)} – {self.end_time.strftime(fmt)}"
        if self.is_overnight:
            label += " 🌙"
        return label


@dataclass(frozen=True)
class HolidayEntity:
    id: int
    name: str
    date: dt.date
    holiday_type: HolidayType
    is_paid: bool
    notes: Optional[str]


@dataclass(frozen=True)
class EmployeeScheduleEntity:
    id: int
    employee_id: int           # FK → employees.id (PK)
    employee_id_str: str       # employees.employee_id (display code)
    employee_name: str
    shift_template_id: Optional[int]
    shift_name: Optional[str]
    date: dt.date
    is_rest_day: bool
    schedule_status: ScheduleStatus
    notes: Optional[str]
    override_start_time: Optional[dt.time]
    override_end_time: Optional[dt.time]
