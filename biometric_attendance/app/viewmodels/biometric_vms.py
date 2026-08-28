"""Biometric ViewModels."""
import asyncio
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot

from biometric_attendance.application.biometrics.device_service import BiometricDeviceService
from biometric_attendance.application.biometrics.enrollment_service import BiometricEnrollmentService
from biometric_attendance.application.biometrics.sync_service import BiometricSyncService
from biometric_attendance.application.services.workforce_service import WorkforceService
from biometric_attendance.core.enums.biometrics import FingerType


class BiometricEnrollmentViewModel(QObject):
    employees_loaded = Signal(list)
    enrolled_fingers_loaded = Signal(list)
    enrollment_progress = Signal(int, str)  # step, message
    enrollment_complete = Signal()
    error_occurred = Signal(str)

    def __init__(
        self,
        workforce_service: WorkforceService,
        enrollment_service: BiometricEnrollmentService,
        adapter_factory,
    ):
        super().__init__()
        self._workforce_service = workforce_service
        self._enrollment_service = enrollment_service
        self._adapter_factory = adapter_factory

    def load_employees(self):
        try:
            emps = self._workforce_service.get_all_employees()
            self.employees_loaded.emit(emps)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load employees: {e}")

    def load_enrolled_fingers(self, employee_id: int):
        try:
            fingers = self._enrollment_service.get_enrolled_fingers(employee_id)
            self.enrolled_fingers_loaded.emit(fingers)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load enrolled fingers: {e}")

    def start_enrollment(self, employee_id: int, finger_type: FingerType):
        import time
        from PySide6.QtWidgets import QApplication
        
        try:
            # Simulated 3-step enrollment for UI
            self.enrollment_progress.emit(1, "Connecting to mock scanner...")
            QApplication.processEvents()
            time.sleep(0.5)
            
            self.enrollment_progress.emit(2, "Capture Sample 1...")
            QApplication.processEvents()
            time.sleep(0.5)
            
            self.enrollment_progress.emit(3, "Capture Sample 2...")
            QApplication.processEvents()
            time.sleep(0.5)
            
            self.enrollment_progress.emit(4, "Capture Sample 3...")
            QApplication.processEvents()
            time.sleep(0.5)

            self.enrollment_progress.emit(5, "Validating quality and saving...")
            QApplication.processEvents()
            time.sleep(0.5)

            # Perform actual logic
            adapter = self._adapter_factory([])
            self._enrollment_service.enroll_fingerprint(employee_id, finger_type, adapter)
            self.enrollment_complete.emit()
        except Exception as e:
            self.error_occurred.emit(f"Enrollment failed: {e}")


class BiometricDevicesViewModel(QObject):
    devices_loaded = Signal(list)
    device_added = Signal()
    connection_tested = Signal(bool, str)
    error_occurred = Signal(str)

    def __init__(self, device_service: BiometricDeviceService):
        super().__init__()
        self._device_service = device_service

    def load_devices(self):
        try:
            devices = self._device_service.get_all_devices()
            self.devices_loaded.emit(devices)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load devices: {e}")

    def add_device(self, name: str, ip: str, port: int):
        try:
            self._device_service.register_device(name, ip, port)
            self.device_added.emit()
        except Exception as e:
            self.error_occurred.emit(f"Failed to add device: {e}")

    def test_connection(self, device_id: int):
        try:
            success = self._device_service.test_connection(device_id)
            msg = "Connection successful!" if success else "Connection failed. See logs."
            self.connection_tested.emit(success, msg)
        except Exception as e:
            self.connection_tested.emit(False, str(e))


class BiometricSyncViewModel(QObject):
    devices_loaded = Signal(list)
    logs_loaded = Signal(list)
    sync_complete = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, device_service: BiometricDeviceService, sync_service: BiometricSyncService):
        super().__init__()
        self._device_service = device_service
        self._sync_service = sync_service

    def load_devices(self):
        try:
            devices = self._device_service.get_all_devices()
            self.devices_loaded.emit(devices)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load devices: {e}")
    
    def load_recent_logs(self):
        try:
            logs = self._sync_service.get_recent_logs()
            self.logs_loaded.emit(logs)
        except Exception as e:
            self.error_occurred.emit(f"Failed to load logs: {e}")

    def pull_logs(self, device_id: int):
        try:
            count = self._sync_service.pull_logs(device_id)
            self.sync_complete.emit(f"Pulled {count} attendance events.")
            self.load_recent_logs()
        except Exception as e:
            self.error_occurred.emit(f"Pull failed: {e}")
            self.load_recent_logs()

    def push_users(self, device_id: int, simulate_failure: bool):
        try:
            count = self._sync_service.push_users(device_id, simulate_failure)
            self.sync_complete.emit(f"Pushed {count} users.")
            self.load_recent_logs()
        except Exception as e:
            self.error_occurred.emit(f"Push failed: {e}")
            self.load_recent_logs()
