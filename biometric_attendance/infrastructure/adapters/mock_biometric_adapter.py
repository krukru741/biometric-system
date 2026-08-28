"""Mock implementation of the biometric device adapter."""
import asyncio
import datetime as dt
import random
from typing import List

from biometric_attendance.core.dtos.biometric_dtos import BiometricAttendanceEvent
from biometric_attendance.core.enums.attendance import AttendanceEventType
from biometric_attendance.core.interfaces.i_biometric_device import IBiometricDevice


class MockBiometricAdapter(IBiometricDevice):
    def __init__(self, active_employee_id_strs: List[str] = None):
        """
        :param active_employee_id_strs: List of string employee IDs (e.g. "EMP-001")
                                        to generate random mock events for.
        """
        self._connected = False
        self._active_employees = active_employee_id_strs or []

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def enroll(self) -> bytes:
        if not self._connected:
            raise ConnectionError("Not connected to mock device.")
        # Simulate an enrollment payload
        return b"MOCK_TEMPLATE_" + str(random.randint(1000, 9999)).encode()

    def verify(self) -> bool:
        if not self._connected:
            raise ConnectionError("Not connected to mock device.")
        return True

    def get_attendance_logs(self) -> List[BiometricAttendanceEvent]:
        """Return a batch of randomized events for active employees."""
        if not self._connected:
            raise ConnectionError("Not connected to mock device.")

        logs = []
        today = dt.date.today()
        for emp_id in self._active_employees:
            # Generate 1 to 4 random events for each employee today
            num_events = random.randint(1, 4)
            for _ in range(num_events):
                event_type = random.choice(list(AttendanceEventType))
                hour = random.randint(7, 18)
                minute = random.randint(0, 59)
                timestamp = dt.datetime(today.year, today.month, today.day, hour, minute, 0)
                logs.append(
                    BiometricAttendanceEvent(
                        employee_id_str=emp_id,
                        event_type=event_type,
                        timestamp=timestamp,
                    )
                )
        
        # Sort logs by timestamp
        logs.sort(key=lambda x: x.timestamp)
        return logs

    def push_user(self, employee_id_str: str, template: bytes) -> bool:
        if not self._connected:
            raise ConnectionError("Not connected to mock device.")
        # Simulate pushing user template to device successfully
        return True
