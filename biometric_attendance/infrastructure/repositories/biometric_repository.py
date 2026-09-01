"""Repositories for the Biometrics domain."""
from __future__ import annotations

from biometric_attendance.infrastructure.data.database import auto_session
import datetime as dt
from typing import List, Optional

from sqlalchemy.orm import Session

from biometric_attendance.core.dtos.biometric_dtos import (
    BiometricDeviceEntity,
    BiometricLogEntity,
    EmployeeBiometricEntity,
)
from biometric_attendance.infrastructure.data.models import (
    BiometricDeviceModel,
    BiometricLogModel,
    EmployeeBiometricModel,
)


class EmployeeBiometricRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _to_entity(self, m: EmployeeBiometricModel) -> EmployeeBiometricEntity:
        return EmployeeBiometricEntity(
            id=m.id,
            employee_id=m.employee_id,
            finger_type=m.finger_type,
            template=m.template,
            template_format=m.template_format,
            device_id=m.device_id,
            created_at=m.created_at,
            updated_at=m.updated_at,
            is_active=m.is_active,
        )

    def save(self, **kwargs) -> EmployeeBiometricEntity:
        with auto_session(self._session) as session:
            m = EmployeeBiometricModel(**kwargs)
            session.add(m)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)

    def get_by_employee_id(self, employee_id: int) -> List[EmployeeBiometricEntity]:
        with auto_session(self._session) as session:
            models = session.query(EmployeeBiometricModel).filter_by(employee_id=employee_id).all()
            return [self._to_entity(m) for m in models]


class BiometricDeviceRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _to_entity(self, m: BiometricDeviceModel) -> BiometricDeviceEntity:
        return BiometricDeviceEntity(
            id=m.id,
            device_name=m.device_name,
            ip_address=m.ip_address,
            port=m.port,
            model=m.model,
            serial_number=m.serial_number,
            firmware_version=m.firmware_version,
            status=m.status,
            last_sync_at=m.last_sync_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
            is_active=m.is_active,
        )

    def get_all(self) -> List[BiometricDeviceEntity]:
        with auto_session(self._session) as session:
            models = session.query(BiometricDeviceModel).all()
            return [self._to_entity(m) for m in models]

    def get_by_id(self, device_id: int) -> Optional[BiometricDeviceEntity]:
        with auto_session(self._session) as session:
            m = session.query(BiometricDeviceModel).filter_by(id=device_id).first()
            return self._to_entity(m) if m else None

    def save(self, **kwargs) -> BiometricDeviceEntity:
        with auto_session(self._session) as session:
            m = BiometricDeviceModel(**kwargs)
            session.add(m)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)
    
    def update(self, device_id: int, **kwargs) -> BiometricDeviceEntity:
        with auto_session(self._session) as session:
            m = session.query(BiometricDeviceModel).filter_by(id=device_id).first()
            if not m:
                raise ValueError(f"Device {device_id} not found")
            for k, v in kwargs.items():
                setattr(m, k, v)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)


class BiometricLogRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session

    def _to_entity(self, m: BiometricLogModel) -> BiometricLogEntity:
        return BiometricLogEntity(
            id=m.id,
            device_id=m.device_id,
            log_type=m.log_type,
            message=m.message,
            raw_payload=m.raw_payload,
            success=m.success,
            timestamp=m.timestamp,
            created_at=m.created_at,
        )

    def save(self, **kwargs) -> BiometricLogEntity:
        with auto_session(self._session) as session:
            m = BiometricLogModel(**kwargs)
            session.add(m)
            session.flush()
            session.refresh(m)
            return self._to_entity(m)

    def get_recent(self, limit: int = 100) -> List[BiometricLogEntity]:
        with auto_session(self._session) as session:
            models = session.query(BiometricLogModel).order_by(BiometricLogModel.created_at.desc()).limit(limit).all()
            return [self._to_entity(m) for m in models]
