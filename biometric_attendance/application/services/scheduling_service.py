"""Application service for Scheduling operations."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from biometric_attendance.core.dtos.scheduling_dtos import (
    EmployeeScheduleEntity,
    HolidayEntity,
    ShiftTemplateEntity,
)
from biometric_attendance.core.enums.scheduling import ScheduleStatus
from biometric_attendance.infrastructure.repositories.scheduling_repository import (
    EmployeeScheduleRepository,
    HolidayRepository,
    ShiftTemplateRepository,
)
from biometric_attendance.infrastructure.repositories.workforce_repository import (
    DepartmentRepository,
    EmployeeRepository,
)


class SchedulingService:
    """Orchestrates Shift Templates, Holidays, and Employee Schedules."""

    def __init__(
        self,
        shift_template_repository: ShiftTemplateRepository,
        holiday_repository: HolidayRepository,
        employee_schedule_repository: EmployeeScheduleRepository,
        employee_repository: EmployeeRepository,
        department_repository: DepartmentRepository,
    ) -> None:
        self._shifts = shift_template_repository
        self._holidays = holiday_repository
        self._schedules = employee_schedule_repository
        self._employees = employee_repository
        self._departments = department_repository

    # -- Shift Templates -------------------------------------------------------

    def get_all_shift_templates(self) -> List[ShiftTemplateEntity]:
        return self._shifts.get_all()

    def get_active_shift_templates(self) -> List[ShiftTemplateEntity]:
        return self._shifts.get_active()

    def create_shift_template(self, **kwargs) -> ShiftTemplateEntity:
        return self._shifts.create(**kwargs)

    def update_shift_template(self, id: int, **kwargs) -> Optional[ShiftTemplateEntity]:
        return self._shifts.update(id=id, **kwargs)

    def deactivate_shift_template(self, id: int) -> bool:
        return self._shifts.deactivate(id=id)

    # -- Holidays --------------------------------------------------------------

    def get_all_holidays(self) -> List[HolidayEntity]:
        return self._holidays.get_all()

    def get_holidays_by_year(self, year: int) -> List[HolidayEntity]:
        return self._holidays.get_by_year(year=year)

    def create_holiday(self, **kwargs) -> HolidayEntity:
        return self._holidays.create(**kwargs)

    def update_holiday(self, id: int, **kwargs) -> Optional[HolidayEntity]:
        return self._holidays.update(id=id, **kwargs)

    def delete_holiday(self, id: int) -> bool:
        return self._holidays.delete(id=id)

    # -- Employee Schedules ----------------------------------------------------

    def get_schedules_for_month(self, year: int, month: int) -> List[EmployeeScheduleEntity]:
        return self._schedules.get_by_month(year=year, month=month)

    def get_schedules_for_employee(
        self, employee_id: int, year: int, month: int
    ) -> List[EmployeeScheduleEntity]:
        return self._schedules.get_by_employee(employee_id=employee_id, year=year, month=month)

    def assign_schedule(
        self,
        employee_id: int,
        date: dt.date,
        shift_template_id: Optional[int],
        is_rest_day: bool = False,
        notes: str = "",
    ) -> EmployeeScheduleEntity:
        """Create or replace a single day's schedule for one employee."""
        # Remove any existing schedule for that day
        existing = (
            self._schedules._session.query(
                __import__(
                    "biometric_attendance.infrastructure.data.models",
                    fromlist=["EmployeeScheduleModel"],
                ).EmployeeScheduleModel
            )
            .filter_by(employee_id=employee_id, date=date)
            .first()
        )
        if existing:
            self._schedules.delete(existing.id)
        return self._schedules.create(
            employee_id=employee_id,
            shift_template_id=shift_template_id,
            date=date,
            is_rest_day=is_rest_day,
            schedule_status=ScheduleStatus.ACTIVE,
            notes=notes,
        )

    def bulk_assign(
        self,
        department_id: Optional[int],
        employee_ids: Optional[List[int]],
        shift_template_id: int,
        start_date: dt.date,
        end_date: dt.date,
    ) -> int:
        """Bulk-assign a shift across a date range.

        - If department_id is given, fetches all Active employees in that dept.
        - Otherwise uses the explicit employee_ids list.
        - D2: Skips days that already have a schedule (skip_existing=True).
        - D3: Skips each employee's configured rest_day automatically.
        """
        # Resolve employee list
        if department_id is not None:
            all_emps = self._employees.get_all()
            emps = [e for e in all_emps if e.department_id == department_id]
        else:
            all_emps = self._employees.get_all()
            emp_id_set = set(employee_ids or [])
            emps = [e for e in all_emps if e.id in emp_id_set]

        if not emps:
            return 0

        emp_ids = [e.id for e in emps]
        rest_day_map = {e.id: e.rest_day for e in emps}

        # Build date list
        dates: list[dt.date] = []
        current = start_date
        while current <= end_date:
            dates.append(current)
            current += dt.timedelta(days=1)

        return self._schedules.bulk_assign(
            employee_ids=emp_ids,
            shift_template_id=shift_template_id,
            dates=dates,
            skip_existing=True,
            skip_rest_days=True,
            rest_day_map=rest_day_map,
        )
