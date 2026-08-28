"""Abstract interface for biometric device adapters."""
from abc import ABC, abstractmethod
from typing import List

from biometric_attendance.core.dtos.biometric_dtos import BiometricAttendanceEvent


class IBiometricDevice(ABC):
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the biometric device."""
        ...

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the biometric device."""
        ...

    @abstractmethod
    def enroll(self) -> bytes:
        """Initiate fingerprint enrollment on the device and return the template blob."""
        ...

    @abstractmethod
    def verify(self) -> bool:
        """Initiate a 1:1 or 1:N verification on the device."""
        ...

    @abstractmethod
    def get_attendance_logs(self) -> List[BiometricAttendanceEvent]:
        """Pull raw attendance logs from the device."""
        ...

    @abstractmethod
    def push_user(self, employee_id_str: str, template: bytes) -> bool:
        """Push an enrolled template to the device."""
        ...
