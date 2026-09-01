"""Repositories for the Scheduling domain."""
from __future__ import annotations

from biometric_attendance.infrastructure.data.database import auto_session
import datetime as dt
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from biometric_attendance.core.dtos.scheduling_dtos import (
    EmployeeScheduleEntity,
    HolidayEntity,
    ShiftTemplateEntity,
)
from biometric_attendance.core.enums.scheduling import HolidayType, ScheduleStatus
from biometric_attendance.infrastructure.data.models import (
    EmployeeScheduleModel,
    HolidayModel,
    ShiftTemplateModel,
    EmployeeModel,
)


class ShiftTemplateRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _to_entity(self, m: ShiftTemplateModel) -> ShiftTemplateEntity:
        return ShiftTemplateEntity(
            id=m.id,
            name=m.name,
            start_time=m.start_time,
            end_time=m.end_time,
            break_start=m.break_start,
            break_end=m.break_end,
            grace_period_mins=m.grace_period_mins,
            late_threshold_mins=m.late_threshold_mins,
            early_out_threshold_mins=m.early_out_threshold_mins,
            overtime_threshold_mins=m.overtime_threshold_mins,
            is_overnight=m.is_overnight,
            is_active=m.is_active,
        )

    def get_all(self) -> List[ShiftTemplateEntity]:
        with auto_session(self._session) as session:
            return [self._to_entity(m) for m in session.query(ShiftTemplateModel).all()]

    def get_active(self) -> List[ShiftTemplateEntity]:
        with auto_session(self._session) as session:
            return [
                self._to_entity(m)
                for m in session.query(ShiftTemplateModel).filter_by(is_active=True).all()
            ]

    def create(self, **kwargs) -> ShiftTemplateEntity:
        # Auto-compute is_overnight
        with auto_session(self._session) as session:
            start = kwargs.get("start_time")
            end = kwargs.get("end_time")
            if start and end:
                kwargs["is_overnight"] = end < start
            m = ShiftTemplateModel(**kwargs)
            session.add(m)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)

    def update(self, id: int, **kwargs) -> Optional[ShiftTemplateEntity]:
        with auto_session(self._session) as session:
            m = session.query(ShiftTemplateModel).filter_by(id=id).first()
            if m is None:
                return None
            for k, v in kwargs.items():
                if hasattr(m, k):
                    setattr(m, k, v)
            # Recompute overnight
            m.is_overnight = m.end_time < m.start_time
            session.flush()
            session.refresh(m)
            return self._to_entity(m)

    def deactivate(self, id: int) -> bool:
        with auto_session(self._session) as session:
            m = session.query(ShiftTemplateModel).filter_by(id=id).first()
            if m is None:
                return False
            m.is_active = False
            session.flush()
            return True


class HolidayRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _to_entity(self, m: HolidayModel) -> HolidayEntity:
        return HolidayEntity(
            id=m.id,
            name=m.name,
            date=m.date,
            holiday_type=m.holiday_type,
            is_paid=m.is_paid,
            notes=m.notes,
        )

    def get_all(self) -> List[HolidayEntity]:
        with auto_session(self._session) as session:
            return [self._to_entity(m) for m in session.query(HolidayModel).order_by(HolidayModel.date).all()]

    def get_by_year(self, year: int) -> List[HolidayEntity]:
        with auto_session(self._session) as session:
            return [
                self._to_entity(m)
                for m in session.query(HolidayModel)
                .filter(HolidayModel.date >= dt.date(year, 1, 1), HolidayModel.date <= dt.date(year, 12, 31))
                .order_by(HolidayModel.date)
                .all()
            ]

    def create(self, **kwargs) -> HolidayEntity:
        with auto_session(self._session) as session:
            m = HolidayModel(**kwargs)
            session.add(m)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)

    def update(self, id: int, **kwargs) -> Optional[HolidayEntity]:
        with auto_session(self._session) as session:
            m = session.query(HolidayModel).filter_by(id=id).first()
            if m is None:
                return None
            for k, v in kwargs.items():
                if hasattr(m, k):
                    setattr(m, k, v)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)

    def delete(self, id: int) -> bool:
        with auto_session(self._session) as session:
            m = session.query(HolidayModel).filter_by(id=id).first()
            if m is None:
                return False
            session.delete(m)
            session.flush()
            return True


class EmployeeScheduleRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _to_entity(self, m: EmployeeScheduleModel) -> EmployeeScheduleEntity:
        emp = m.employee
        shift = m.shift_template
        return EmployeeScheduleEntity(
            id=m.id,
            employee_id=m.employee_id,
            employee_id_str=emp.employee_id if emp else "",
            employee_name=f"{emp.first_name} {emp.last_name}" if emp else "",
            shift_template_id=m.shift_template_id,
            shift_name=shift.name if shift else None,
            date=m.date,
            is_rest_day=m.is_rest_day,
            schedule_status=m.schedule_status,
            notes=m.notes,
            override_start_time=m.override_start_time,
            override_end_time=m.override_end_time,
        )

    def _base_query(self):
        return (
            self._session.query(EmployeeScheduleModel)
            .options(
                joinedload(EmployeeScheduleModel.employee),
                joinedload(EmployeeScheduleModel.shift_template),
            )
        )

    def get_by_month(self, year: int, month: int) -> List[EmployeeScheduleEntity]:
        with auto_session(self._session) as session:
            start = dt.date(year, month, 1)
            if month == 12:
                end = dt.date(year + 1, 1, 1)
            else:
                end = dt.date(year, month + 1, 1)
            rows = (
                self._base_query()
                .filter(EmployeeScheduleModel.date >= start, EmployeeScheduleModel.date < end)
                .all()
            )
            return [self._to_entity(r) for r in rows]

    def get_by_employee(self, employee_id: int, year: int, month: int) -> List[EmployeeScheduleEntity]:
        with auto_session(self._session) as session:
            start = dt.date(year, month, 1)
            if month == 12:
                end = dt.date(year + 1, 1, 1)
            else:
                end = dt.date(year, month + 1, 1)
            rows = (
                self._base_query()
                .filter(
                    EmployeeScheduleModel.employee_id == employee_id,
                    EmployeeScheduleModel.date >= start,
                    EmployeeScheduleModel.date < end,
                )
                .all()
            )
            return [self._to_entity(r) for r in rows]

    def get_schedules(
        self,
        employee_id: Optional[int] = None,
        start_date: Optional[dt.date] = None,
        end_date: Optional[dt.date] = None,
    ) -> List[EmployeeScheduleEntity]:
        with auto_session(self._session) as session:
            query = self._base_query()
            if employee_id is not None:
                query = query.filter(EmployeeScheduleModel.employee_id == employee_id)
            if start_date is not None:
                query = query.filter(EmployeeScheduleModel.date >= start_date)
            if end_date is not None:
                query = query.filter(EmployeeScheduleModel.date <= end_date)
            
            query = query.order_by(EmployeeScheduleModel.date.desc(), EmployeeScheduleModel.employee_id)
            return [self._to_entity(r) for r in query.all()]

    def create(self, **kwargs) -> EmployeeScheduleEntity:
        with auto_session(self._session) as session:
            m = EmployeeScheduleModel(**kwargs)
            session.add(m)
            session.flush()
            session.refresh(m)
            # Reload with joins
            return self._to_entity(self._base_query().filter_by(id=m.id).first())

    def update(self, id: int, **kwargs) -> Optional[EmployeeScheduleEntity]:
        with auto_session(self._session) as session:
            m = session.query(EmployeeScheduleModel).filter_by(id=id).first()
            if m is None:
                return None
            for k, v in kwargs.items():
                if hasattr(m, k):
                    setattr(m, k, v)
            session.flush()
            return self._to_entity(self._base_query().filter_by(id=id).first())

    def delete(self, id: int) -> bool:
        with auto_session(self._session) as session:
            m = session.query(EmployeeScheduleModel).filter_by(id=id).first()
            if m is None:
                return False
            session.delete(m)
            session.flush()
            return True

    def bulk_assign(
        self,
        employee_ids: List[int],
        shift_template_id: int,
        dates: List[dt.date],
        skip_existing: bool = True,
        skip_rest_days: bool = True,
        rest_day_map: dict[int, str] | None = None,
    ) -> int:
        with auto_session(self._session) as session:
            """Assign a shift to multiple employees across multiple dates.
    
            Returns the count of new schedule rows created.
            rest_day_map: {employee_id: rest_day_name} e.g. {1: "Sunday"}
            """
            # Build set of (employee_id, date) that already have schedules
            existing: set[tuple[int, dt.date]] = set()
            if skip_existing:
                existing_rows = (
                    session.query(
                        EmployeeScheduleModel.employee_id,
                        EmployeeScheduleModel.date,
                    )
                    .filter(
                        EmployeeScheduleModel.employee_id.in_(employee_ids),
                        EmployeeScheduleModel.date.in_(dates),
                    )
                    .all()
                )
                existing = {(r.employee_id, r.date) for r in existing_rows}
    
            # Weekday name mapping (Python weekday: 0=Monday, 6=Sunday)
            _WEEKDAY_NAMES = [
                "Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday",
            ]
    
            count = 0
            for emp_id in employee_ids:
                emp_rest_day = (rest_day_map or {}).get(emp_id, "Sunday") if skip_rest_days else None
                for d in dates:
                    if skip_existing and (emp_id, d) in existing:
                        continue
                    if emp_rest_day and _WEEKDAY_NAMES[d.weekday()] == emp_rest_day:
                        continue
                    new_row = EmployeeScheduleModel(
                        employee_id=emp_id,
                        shift_template_id=shift_template_id,
                        date=d,
                        is_rest_day=False,
                        schedule_status=ScheduleStatus.ACTIVE,
                    )
                    session.add(new_row)
                    count += 1
            session.flush()
            return count
