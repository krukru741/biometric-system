"""Biometric Sync Service."""
import datetime as dt

from biometric_attendance.application.attendance.event_service import AttendanceEventService
from biometric_attendance.core.enums.attendance import AttendanceSource
from biometric_attendance.core.enums.biometrics import BiometricLogType, DeviceStatus
from biometric_attendance.core.interfaces.i_biometric_device import IBiometricDevice
from biometric_attendance.infrastructure.repositories.biometric_repository import (
    BiometricDeviceRepository,
    BiometricLogRepository,
    EmployeeBiometricRepository,
)
from biometric_attendance.infrastructure.repositories.workforce_repository import EmployeeRepository
from biometric_attendance.application.biometrics.encryption_service import BiometricEncryptionService


class BiometricSyncService:
    def __init__(
        self,
        device_repo: BiometricDeviceRepository,
        log_repo: BiometricLogRepository,
        employee_repo: EmployeeRepository,
        biometric_repo: EmployeeBiometricRepository,
        attendance_event_svc: AttendanceEventService,
        encryption_service: BiometricEncryptionService,
        adapter_factory,  # Callable[[], IBiometricDevice]
    ):
        self._device_repo = device_repo
        self._log_repo = log_repo
        self._employee_repo = employee_repo
        self._biometric_repo = biometric_repo
        self._attendance_event_svc = attendance_event_svc
        self._encryption_service = encryption_service
        self._adapter_factory = adapter_factory

    def _log(self, device_id: int, log_type: BiometricLogType, success: bool, message: str, payload: str = None):
        self._log_repo.save(
            device_id=device_id,
            log_type=log_type,
            success=success,
            message=message,
            raw_payload=payload
        )

    def pull_logs(self, device_id: int) -> int:
        """Pulls raw logs from device and passes them to the attendance engine."""
        device_entity = self._device_repo.get_by_id(device_id)
        if not device_entity:
            raise ValueError("Device not found")
        
        # Resolve string IDs to DB employee IDs
        employees = self._employee_repo.get_all()
        emp_map = {emp.employee_id: emp.id for emp in employees}
        active_emp_strs = [emp.employee_id for emp in employees if emp.is_active]

        adapter: IBiometricDevice = self._adapter_factory(active_emp_strs)
        try:
            adapter.connect()
            raw_events = adapter.get_attendance_logs()
            adapter.disconnect()
        except Exception as e:
            self._log(device_id, BiometricLogType.PULL_LOGS, False, f"Failed to pull logs: {e}")
            self._device_repo.update(device_id, status=DeviceStatus.OFFLINE)
            raise


        processed_count = 0
        for ev in raw_events:
            emp_id = emp_map.get(ev.employee_id_str)
            if not emp_id:
                # Employee not in DB, skip
                continue
            
            # Feed into Attendance Engine
            self._attendance_event_svc.record_event(
                employee_id=emp_id,
                event_type=ev.event_type,
                timestamp=ev.timestamp,
                source=AttendanceSource.BIOMETRIC,
                device_id=str(device_entity.id),
                biometric_verified=True,
            )
            processed_count += 1
        
        self._log(device_id, BiometricLogType.PULL_LOGS, True, f"Successfully pulled {processed_count} logs.")
        self._device_repo.update(device_id, last_sync_at=dt.datetime.now(), status=DeviceStatus.ONLINE)
        return processed_count

    def push_users(self, device_id: int, simulate_failure: bool = False) -> int:
        """Pushes active user templates to the device."""
        device_entity = self._device_repo.get_by_id(device_id)
        if not device_entity:
            raise ValueError("Device not found")
        
        if simulate_failure:
            self._log(device_id, BiometricLogType.PUSH_USER, False, "Simulated network failure during push")
            self._device_repo.update(device_id, status=DeviceStatus.OFFLINE)
            raise ConnectionError("Simulated network failure")

        adapter: IBiometricDevice = self._adapter_factory([])
        try:
            adapter.connect()
        except Exception as e:
            self._log(device_id, BiometricLogType.PUSH_USER, False, f"Failed to connect: {e}")
            self._device_repo.update(device_id, status=DeviceStatus.OFFLINE)
            raise

        employees = self._employee_repo.get_active()
        pushed_count = 0
        try:
            for emp in employees:
                biometrics = self._biometric_repo.get_by_employee_id(emp.id)
                for bio in biometrics:
                    if bio.is_active:
                        decrypted_template = self._encryption_service.decrypt(bio.template)
                        adapter.push_user(emp.employee_id, decrypted_template)
                        pushed_count += 1
            adapter.disconnect()
        except Exception as e:
            self._log(device_id, BiometricLogType.PUSH_USER, False, f"Error during push: {e}")
            raise
        
        self._log(device_id, BiometricLogType.PUSH_USER, True, f"Successfully pushed {pushed_count} templates.")
        self._device_repo.update(device_id, last_sync_at=dt.datetime.now(), status=DeviceStatus.ONLINE)
        return pushed_count

    def get_recent_logs(self, limit: int = 100):
        return self._log_repo.get_recent(limit=limit)
