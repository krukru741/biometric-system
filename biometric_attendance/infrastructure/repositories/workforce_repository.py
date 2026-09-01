"""Concrete SQLAlchemy repositories for Workforce entities."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity, PositionEntity
from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType
from biometric_attendance.infrastructure.data.models import DepartmentModel, EmployeeModel, PositionModel


class DepartmentRepository:
    def __init__(self, ) -> None:
        pass

    def _to_entity(self, model: DepartmentModel) -> DepartmentEntity:
        return DepartmentEntity(
            id=model.id,
            name=model.name,
            description=model.description,
            is_active=model.is_active,
        )

    def get_all(self) -> List[DepartmentEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            models = session.query(DepartmentModel).all()
            return [self._to_entity(m) for m in models]

    def create(self, name: str, description: str, is_active: bool = True) -> DepartmentEntity:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = DepartmentModel(name=name, description=description, is_active=is_active)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def update(self, id: int, name: str, description: str, is_active: bool = True) -> Optional[DepartmentEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = session.query(DepartmentModel).filter_by(id=id).first()
            if model is None:
                return None
            model.name = name
            model.description = description
            model.is_active = is_active
            session.commit()
            session.refresh(model)
            return self._to_entity(model)


class PositionRepository:
    def __init__(self, ) -> None:
        pass

    def _to_entity(self, model: PositionModel) -> PositionEntity:
        return PositionEntity(
            id=model.id,
            name=model.name,
            description=model.description,
            department_id=model.department_id,
            is_active=model.is_active,
            department_name=model.department.name if model.department else None,
        )

    def get_all(self) -> List[PositionEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            models = session.query(PositionModel).options(joinedload(PositionModel.department)).all()
            return [self._to_entity(m) for m in models]

    def create(
        self, name: str, description: str, department_id: Optional[int], is_active: bool = True
    ) -> PositionEntity:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = PositionModel(
                name=name,
                description=description,
                department_id=department_id,
                is_active=is_active,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def update(
        self, id: int, name: str, description: str, department_id: Optional[int], is_active: bool = True
    ) -> Optional[PositionEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = (
                session.query(PositionModel)
                .options(joinedload(PositionModel.department))
                .filter_by(id=id)
                .first()
            )
            if model is None:
                return None
            model.name = name
            model.description = description
            model.department_id = department_id
            model.is_active = is_active
            session.commit()
            session.refresh(model)
            return self._to_entity(model)


class EmployeeRepository:
    def __init__(self, ) -> None:
        pass

    def _to_entity(self, model: EmployeeModel) -> EmployeeEntity:
        return EmployeeEntity(
            id=model.id,
            employee_id=model.employee_id,
            first_name=model.first_name,
            middle_name=model.middle_name,
            last_name=model.last_name,
            suffix=model.suffix,
            birth_date=model.birth_date,
            gender=model.gender,
            phone=model.phone,
            email=model.email,
            address=model.address,
            photo_path=model.photo_path,
            department_id=model.department_id,
            department_name=model.department.name if model.department else None,
            position_id=model.position_id,
            position_name=model.position.name if model.position else None,
            employment_type=model.employment_type,
            date_hired=model.date_hired,
            status=model.status,
            supervisor_id=model.supervisor_id,
            grace_period_mins=model.grace_period_mins,
            overtime_eligible=model.overtime_eligible,
            rest_day=model.rest_day,
        )

    def get_all(self) -> List[EmployeeEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            models = (
                session.query(EmployeeModel)
                .options(joinedload(EmployeeModel.department), joinedload(EmployeeModel.position))
                .all()
            )
            return [self._to_entity(m) for m in models]

    def create(self, **kwargs) -> EmployeeEntity:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = EmployeeModel(**kwargs)
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def update(self, id: int, **kwargs) -> Optional[EmployeeEntity]:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = (
                session.query(EmployeeModel)
                .options(joinedload(EmployeeModel.department), joinedload(EmployeeModel.position))
                .filter_by(id=id)
                .first()
            )
            if model is None:
                return None
            for key, value in kwargs.items():
                if hasattr(model, key):
                    setattr(model, key, value)
            session.commit()
            session.refresh(model)
            return self._to_entity(model)

    def archive(self, id: int) -> bool:
        from biometric_attendance.infrastructure.data.database import get_session
        with get_session() as session:
            model = session.query(EmployeeModel).filter_by(id=id).first()
            if model is None:
                return False
            model.status = EmploymentStatus.ARCHIVED
            session.commit()
            return True
