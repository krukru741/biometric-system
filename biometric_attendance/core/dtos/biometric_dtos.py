"""DTOs for the Biometrics domain."""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Optional

from biometric_attendance.core.enums.biometrics import (
    BiometricLogType,
    DeviceStatus,
    FingerType,
)
from biometric_attendance.core.enums.attendance import AttendanceEventType


@dataclass(frozen=True)
class EmployeeBiometricEntity:
    id: int
    employee_id: int
    finger_type: FingerType
    template: bytes
    template_format: str
    device_id: Optional[int]
    created_at: dt.datetime
    updated_at: dt.datetime
    is_active: bool


@dataclass(frozen=True)
class BiometricDeviceEntity:
    id: int
    device_name: str
    ip_address: str
    port: int
    model: str
    serial_number: str
    firmware_version: str
    status: DeviceStatus
    last_sync_at: Optional[dt.datetime]
    created_at: dt.datetime
    updated_at: dt.datetime
    is_active: bool


@dataclass(frozen=True)
class BiometricLogEntity:
    id: int
    device_id: int
    log_type: BiometricLogType
    message: str
    raw_payload: Optional[str]
    success: bool
    timestamp: dt.datetime
    created_at: dt.datetime


@dataclass(frozen=True)
class BiometricAttendanceEvent:
    """Temporary DTO for raw events pulled from the device, before they become AttendanceEventEntity."""
    employee_id_str: str  # Usually the string ID (e.g. "EMP-001") stored on the device
    event_type: AttendanceEventType
    timestamp: dt.datetime
