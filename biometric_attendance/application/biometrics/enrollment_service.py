"""Biometric Enrollment Service."""
from typing import List

from biometric_attendance.application.biometrics.encryption_service import BiometricEncryptionService
from biometric_attendance.core.dtos.biometric_dtos import EmployeeBiometricEntity
from biometric_attendance.core.enums.biometrics import FingerType
from biometric_attendance.core.interfaces.i_biometric_device import IBiometricDevice
from biometric_attendance.infrastructure.repositories.biometric_repository import EmployeeBiometricRepository


class BiometricEnrollmentService:
    def __init__(
        self,
        repository: EmployeeBiometricRepository,
        encryption_service: BiometricEncryptionService,
    ):
        self._repository = repository
        self._encryption_service = encryption_service

    def get_enrolled_fingers(self, employee_id: int) -> List[FingerType]:
        records = self._repository.get_by_employee_id(employee_id)
        return [r.finger_type for r in records if r.is_active]

    def enroll_fingerprint(
        self,
        employee_id: int,
        finger_type: FingerType,
        device: IBiometricDevice,
    ) -> EmployeeBiometricEntity:
        """Capture a fingerprint from the device and store it encrypted."""
        # 1. Capture from device
        device.connect()
        try:
            raw_template = device.enroll()
        finally:
            device.disconnect()

        # 2. Encrypt template
        encrypted_template = self._encryption_service.encrypt(raw_template)

        # 3. Store in DB
        return self._repository.save(
            employee_id=employee_id,
            finger_type=finger_type,
            template=encrypted_template,
            template_format="mock",
            is_active=True,
        )
