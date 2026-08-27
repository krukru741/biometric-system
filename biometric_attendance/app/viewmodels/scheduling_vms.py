"""ViewModels for the Scheduling module."""
from __future__ import annotations

import calendar
import datetime as dt
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot

from biometric_attendance.application.services.scheduling_service import SchedulingService
from biometric_attendance.core.dtos.scheduling_dtos import (
    EmployeeScheduleEntity,
    HolidayEntity,
    ShiftTemplateEntity,
)
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity


class ShiftTemplatesViewModel(QObject):
    error_occurred = Signal(str)
    shifts_loaded = Signal(list)  # list[ShiftTemplateEntity]

    def __init__(self, service: SchedulingService) -> None:
        super().__init__()
        self._service = service

    def load_shifts(self) -> None:
        try:
            self.shifts_loaded.emit(self._service.get_all_shift_templates())
        except Exception as e:
            self.error_occurred.emit(str(e))

    def create_shift(self, **kwargs) -> None:
        try:
            self._service.create_shift_template(**kwargs)
            self.load_shifts()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def update_shift(self, id: int, **kwargs) -> None:
        try:
            self._service.update_shift_template(id=id, **kwargs)
            self.load_shifts()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def deactivate_shift(self, id: int) -> None:
        try:
            self._service.deactivate_shift_template(id=id)
            self.load_shifts()
        except Exception as e:
            self.error_occurred.emit(str(e))


class HolidaysViewModel(QObject):
    error_occurred = Signal(str)
    holidays_loaded = Signal(list)  # list[HolidayEntity]

    def __init__(self, service: SchedulingService) -> None:
        super().__init__()
        self._service = service
        self._current_year = dt.date.today().year

    def load_holidays(self, year: Optional[int] = None) -> None:
        try:
            y = year or self._current_year
            self._current_year = y
            self.holidays_loaded.emit(self._service.get_holidays_by_year(y))
        except Exception as e:
            self.error_occurred.emit(str(e))

    def create_holiday(self, **kwargs) -> None:
        try:
            self._service.create_holiday(**kwargs)
            self.load_holidays()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def update_holiday(self, id: int, **kwargs) -> None:
        try:
            self._service.update_holiday(id=id, **kwargs)
            self.load_holidays()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def delete_holiday(self, id: int) -> None:
        try:
            self._service.delete_holiday(id=id)
            self.load_holidays()
        except Exception as e:
            self.error_occurred.emit(str(e))


class ScheduleCalendarViewModel(QObject):
    error_occurred = Signal(str)
    schedules_loaded = Signal(list)   # list[EmployeeScheduleEntity]
    employees_loaded = Signal(list)   # list[EmployeeEntity]
    departments_loaded = Signal(list) # list[DepartmentEntity]
    shifts_loaded = Signal(list)      # list[ShiftTemplateEntity]
    bulk_assign_done = Signal(int)    # count assigned

    def __init__(self, service: SchedulingService) -> None:
        super().__init__()
        self._service = service
        today = dt.date.today()
        self._year = today.year
        self._month = today.month

    def load_month(self, year: int, month: int) -> None:
        try:
            self._year = year
            self._month = month
            schedules = self._service.get_schedules_for_month(year, month)
            self.schedules_loaded.emit(schedules)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_supporting_data(self) -> None:
        """Load employees, departments and shift templates for filters/dialogs."""
        try:
            # Reuse the underlying repositories via the service
            emps = self._service._employees.get_all()
            self.employees_loaded.emit(emps)
            depts = self._service._departments.get_all()
            self.departments_loaded.emit(depts)
            shifts = self._service.get_active_shift_templates()
            self.shifts_loaded.emit(shifts)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def assign_schedule(
        self,
        employee_id: int,
        date: dt.date,
        shift_template_id: Optional[int],
        is_rest_day: bool,
        notes: str = "",
    ) -> None:
        try:
            self._service.assign_schedule(
                employee_id=employee_id,
                date=date,
                shift_template_id=shift_template_id,
                is_rest_day=is_rest_day,
                notes=notes,
            )
            self.load_month(self._year, self._month)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def bulk_assign(
        self,
        department_id: Optional[int],
        employee_ids: Optional[list[int]],
        shift_template_id: int,
        start_date: dt.date,
        end_date: dt.date,
    ) -> None:
        try:
            count = self._service.bulk_assign(
                department_id=department_id,
                employee_ids=employee_ids,
                shift_template_id=shift_template_id,
                start_date=start_date,
                end_date=end_date,
            )
            self.bulk_assign_done.emit(count)
            self.load_month(self._year, self._month)
        except Exception as e:
            self.error_occurred.emit(str(e))
