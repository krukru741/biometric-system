"""Biometric Device Service."""
import datetime as dt
from typing import List

from biometric_attendance.core.dtos.biometric_dtos import BiometricDeviceEntity
from biometric_attendance.core.enums.biometrics import BiometricLogType, DeviceStatus
from biometric_attendance.core.interfaces.i_biometric_device import IBiometricDevice
from biometric_attendance.infrastructure.repositories.biometric_repository import (
    BiometricDeviceRepository,
    BiometricLogRepository,
)


class BiometricDeviceService:
    def __init__(
        self,
        device_repo: BiometricDeviceRepository,
        log_repo: BiometricLogRepository,
        adapter_factory,  # Callable[[], IBiometricDevice]
    ):
        self._device_repo = device_repo
        self._log_repo = log_repo
        self._adapter_factory = adapter_factory

    def get_all_devices(self) -> List[BiometricDeviceEntity]:
        return self._device_repo.get_all()
    
    def register_device(self, name: str, ip: str, port: int) -> BiometricDeviceEntity:
        return self._device_repo.save(
            device_name=name,
            ip_address=ip,
            port=port,
            status=DeviceStatus.UNKNOWN,
        )
    
    def _log(self, device_id: int, log_type: BiometricLogType, success: bool, message: str, payload: str = None):
        self._log_repo.save(
            device_id=device_id,
            log_type=log_type,
            success=success,
            message=message,
            raw_payload=payload
        )

    def test_connection(self, device_id: int) -> bool:
        device_entity = self._device_repo.get_by_id(device_id)
        if not device_entity:
            raise ValueError("Device not found")
        
        adapter: IBiometricDevice = self._adapter_factory(device_entity)
        success = False
        message = ""
        try:
            adapter.connect()
            success = True
            message = "Connection successful"
            adapter.disconnect()
        except Exception as e:
            success = False
            message = f"Connection failed: {e}"
        
        # Log the result
        self._log(device_id, BiometricLogType.CONNECTION_TEST, success, message)
        
        # Update device status
        new_status = DeviceStatus.ONLINE if success else DeviceStatus.OFFLINE
        self._device_repo.update(device_id, status=new_status)
        return success
