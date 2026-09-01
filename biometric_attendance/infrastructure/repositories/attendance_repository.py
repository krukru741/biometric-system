"""Repositories for the Attendance domain."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from biometric_attendance.core.dtos.attendance_dtos import (
    AttendanceCorrectionEntity,
    AttendanceEventEntity,
    AttendanceRecordEntity,
)
from biometric_attendance.core.enums.attendance import (
    AttendanceStatus,
    CorrectionStatus,
)
from biometric_attendance.infrastructure.data.models import (
    AttendanceCorrectionModel,
    AttendanceEventModel,
    AttendanceRecordModel,
    EmployeeModel,
    EmployeeScheduleModel,
)


class AttendanceEventRepository:
    def __init__(self, ) -> None:
        pass

    def _to_entity(self, m: AttendanceEventModel) -> AttendanceEventEntity:
        emp = m.employee
        return AttendanceEventEntity(
            id=m.id,
            employee_id=m.employee_id,
            employee_id_str=emp.employee_id if emp else "",
            employee_name=f"{emp.first_name} {emp.last_name}" if emp else "",
            device_id=m.device_id,
            event_type=m.event_type,
            timestamp=m.timestamp,
            biometric_verified=m.biometric_verified,
            source=m.source,
            created_at=m.created_at,
        )

    def _base_query(self):
        return (
            self._session.query(AttendanceEventModel)
            .options(joinedload(AttendanceEventModel.employee))
        )

    def save(self, **kwargs) -> AttendanceEventEntity:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            m = AttendanceEventModel(**kwargs)
            session.add(m)
            session.commit()
            session.refresh(m)
            return self._to_entity(self._base_query().filter_by(id=m.id).first())

    def get_by_employee_and_date(
        self, employee_id: int, date: dt.date
    ) -> List[AttendanceEventEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            start = dt.datetime.combine(date, dt.time.min)
            end = dt.datetime.combine(date, dt.time.max)
            rows = (
                self._base_query()
                .filter(
                    AttendanceEventModel.employee_id == employee_id,
                    AttendanceEventModel.timestamp >= start,
                    AttendanceEventModel.timestamp <= end,
                )
                .order_by(AttendanceEventModel.timestamp)
                .all()
            )
            return [self._to_entity(r) for r in rows]

    def get_recent_events(
        self, employee_id: int, since: dt.datetime
    ) -> List[AttendanceEventEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            """Return events for an employee since a given datetime (for duplicate detection)."""
            rows = (
                self._base_query()
                .filter(
                    AttendanceEventModel.employee_id == employee_id,
                    AttendanceEventModel.timestamp >= since,
                )
                .order_by(AttendanceEventModel.timestamp.desc())
                .all()
            )
            return [self._to_entity(r) for r in rows]

    def get_by_date_range(
        self,
        start_date: dt.date,
        end_date: dt.date,
        employee_id: Optional[int] = None,
    ) -> List[AttendanceEventEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            start = dt.datetime.combine(start_date, dt.time.min)
            end = dt.datetime.combine(end_date, dt.time.max)
            query = self._base_query().filter(
                AttendanceEventModel.timestamp >= start,
                AttendanceEventModel.timestamp <= end,
            )
            if employee_id is not None:
                query = query.filter(AttendanceEventModel.employee_id == employee_id)
            return [self._to_entity(r) for r in query.order_by(AttendanceEventModel.timestamp).all()]


class AttendanceRecordRepository:
    def __init__(self, ) -> None:
        pass

    def _to_entity(self, m: AttendanceRecordModel) -> AttendanceRecordEntity:
        emp = m.employee
        return AttendanceRecordEntity(
            id=m.id,
            employee_id=m.employee_id,
            employee_id_str=emp.employee_id if emp else "",
            employee_name=f"{emp.first_name} {emp.last_name}" if emp else "",
            schedule_id=m.schedule_id,
            date=m.date,
            time_in=m.time_in,
            break_out=m.break_out,
            break_in=m.break_in,
            time_out=m.time_out,
            worked_minutes=m.worked_minutes,
            late_minutes=m.late_minutes,
            undertime_minutes=m.undertime_minutes,
            overtime_minutes=m.overtime_minutes,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _base_query(self):
        return (
            self._session.query(AttendanceRecordModel)
            .options(joinedload(AttendanceRecordModel.employee))
        )

    def get_or_create_for_date(
        self,
        employee_id: int,
        date: dt.date,
        schedule_id: Optional[int] = None,
    ) -> tuple[AttendanceRecordModel, bool]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            """Return (model, is_new).
    
            Overnight routing: if no record exists for `date`, check the previous
            day for an open (time_out IS NULL) record — if found, that record owns
            this OUT event (per Q2: attendance date = IN date).
            """
            existing = (
                session.query(AttendanceRecordModel)
                .filter_by(employee_id=employee_id, date=date)
                .first()
            )
            if existing:
                return existing, False
    
            # Overnight check: look for an open record from the previous calendar day
            prev_date = date - dt.timedelta(days=1)
            prev_record = (
                session.query(AttendanceRecordModel)
                .filter(
                    AttendanceRecordModel.employee_id == employee_id,
                    AttendanceRecordModel.date == prev_date,
                    AttendanceRecordModel.time_out.is_(None),
                )
                .first()
            )
            if prev_record is not None:
                # The OUT event belongs to the overnight record started yesterday
                return prev_record, False
    
            # Create new record
            new_record = AttendanceRecordModel(
                employee_id=employee_id,
                date=date,
                schedule_id=schedule_id,
                status=AttendanceStatus.INCOMPLETE,
                worked_minutes=0,
                late_minutes=0,
                undertime_minutes=0,
                overtime_minutes=0,
            )
            session.add(new_record)
            session.flush()
            return new_record, True

    def save_model(self, model: AttendanceRecordModel) -> AttendanceRecordEntity:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            session.commit()
            session.refresh(model)
            return self._to_entity(self._base_query().filter_by(id=model.id).first())

    def get_by_employee_and_date(
        self, employee_id: int, date: dt.date
    ) -> Optional[AttendanceRecordEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            m = (
                self._base_query()
                .filter_by(employee_id=employee_id, date=date)
                .first()
            )
            return self._to_entity(m) if m else None

    def get_by_date_range(
        self,
        start_date: dt.date,
        end_date: dt.date,
        employee_id: Optional[int] = None,
    ) -> List[AttendanceRecordEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            query = self._base_query().filter(
                AttendanceRecordModel.date >= start_date,
                AttendanceRecordModel.date <= end_date,
            )
            if employee_id is not None:
                query = query.filter(AttendanceRecordModel.employee_id == employee_id)
            return [
                self._to_entity(r)
                for r in query.order_by(
                    AttendanceRecordModel.date.desc(),
                    AttendanceRecordModel.employee_id,
                ).all()
            ]

    def create_absent_records(
        self,
        date: dt.date,
        employee_ids: List[int],
    ) -> int:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            """Create ABSENT records for employees with no record on the given date.
    
            Called by the manual 'Generate Absent Records' button in the UI.
            Skips employees who already have a record for that date.
            Returns the count of records created.
            """
            existing_ids = {
                row.employee_id
                for row in session.query(AttendanceRecordModel.employee_id)
                .filter_by(date=date)
                .all()
            }
            count = 0
            for emp_id in employee_ids:
                if emp_id not in existing_ids:
                    m = AttendanceRecordModel(
                        employee_id=emp_id,
                        date=date,
                        status=AttendanceStatus.ABSENT,
                        worked_minutes=0,
                        late_minutes=0,
                        undertime_minutes=0,
                        overtime_minutes=0,
                    )
                    session.add(m)
                    count += 1
            session.commit()
            return count


class AttendanceCorrectionRepository:
    def __init__(self, ) -> None:
        pass

    def _to_entity(self, m: AttendanceCorrectionModel) -> AttendanceCorrectionEntity:
        emp = m.employee
        return AttendanceCorrectionEntity(
            id=m.id,
            attendance_record_id=m.attendance_record_id,
            employee_id=m.employee_id,
            employee_id_str=emp.employee_id if emp else "",
            employee_name=f"{emp.first_name} {emp.last_name}" if emp else "",
            correction_type=m.correction_type,
            original_value=m.original_value,
            requested_value=m.requested_value,
            reason=m.reason,
            attachment_path=m.attachment_path,
            status=m.status,
            requested_by=m.requested_by,
            requested_at=m.requested_at,
            reviewed_by=m.reviewed_by,
            reviewed_at=m.reviewed_at,
            review_comment=m.review_comment,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _base_query(self):
        return (
            self._session.query(AttendanceCorrectionModel)
            .options(joinedload(AttendanceCorrectionModel.employee))
        )

    def create(self, **kwargs) -> AttendanceCorrectionEntity:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            m = AttendanceCorrectionModel(**kwargs)
            session.add(m)
            session.commit()
            session.refresh(m)
            return self._to_entity(self._base_query().filter_by(id=m.id).first())

    def update_status(
        self,
        correction_id: int,
        status: CorrectionStatus,
        reviewer_id: int,
        reviewed_at: dt.datetime,
        comment: Optional[str] = None,
    ) -> Optional[AttendanceCorrectionEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            m = session.query(AttendanceCorrectionModel).filter_by(id=correction_id).first()
            if m is None:
                return None
            m.status = status
            m.reviewed_by = reviewer_id
            m.reviewed_at = reviewed_at
            m.review_comment = comment
            session.commit()
            return self._to_entity(self._base_query().filter_by(id=correction_id).first())

    def get_pending(self) -> List[AttendanceCorrectionEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            rows = (
                self._base_query()
                .filter_by(status=CorrectionStatus.PENDING)
                .order_by(AttendanceCorrectionModel.requested_at)
                .all()
            )
            return [self._to_entity(r) for r in rows]

    def get_by_record(self, record_id: int) -> List[AttendanceCorrectionEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            rows = (
                self._base_query()
                .filter_by(attendance_record_id=record_id)
                .order_by(AttendanceCorrectionModel.requested_at)
                .all()
            )
            return [self._to_entity(r) for r in rows]

    def get_by_employee(self, employee_id: int) -> List[AttendanceCorrectionEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            rows = (
                self._base_query()
                .filter_by(employee_id=employee_id)
                .order_by(AttendanceCorrectionModel.requested_at.desc())
                .all()
            )
            return [self._to_entity(r) for r in rows]
