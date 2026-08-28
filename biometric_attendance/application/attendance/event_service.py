"""AttendanceEventService — high-level service for recording and querying raw events."""
from __future__ import annotations

import datetime as dt
from typing import List, Optional

from biometric_attendance.core.dtos.attendance_dtos import (
    AttendanceEventEntity,
    ProcessEventResult,
)
from biometric_attendance.core.enums.attendance import (
    AttendanceEventType,
    AttendanceSource,
)
from biometric_attendance.core.interfaces.i_attendance_interfaces import (
    IAttendanceEventService,
    IAttendanceProcessor,
)
from biometric_attendance.infrastructure.repositories.attendance_repository import (
    AttendanceEventRepository,
)


class AttendanceEventService(IAttendanceEventService):
    def __init__(
        self,
        event_repository: AttendanceEventRepository,
        processor: IAttendanceProcessor,
    ) -> None:
        self._events = event_repository
        self._processor = processor

    def record_event(
        self,
        employee_id: int,
        event_type: AttendanceEventType,
        timestamp: dt.datetime,
        device_id: Optional[str] = None,
        biometric_verified: bool = False,
        source: AttendanceSource = AttendanceSource.MANUAL,
    ) -> ProcessEventResult:
        """Persist the raw event then run the processor pipeline."""
        event_entity = self._events.save(
            employee_id=employee_id,
            event_type=event_type,
            timestamp=timestamp,
            device_id=device_id,
            biometric_verified=biometric_verified,
            source=source,
        )
        return self._processor.process_event(event_entity)

    def get_events(self, employee_id: int, date: dt.date) -> List[AttendanceEventEntity]:
        return self._events.get_by_employee_and_date(employee_id=employee_id, date=date)
