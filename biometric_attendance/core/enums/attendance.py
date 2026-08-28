"""Enums for the Attendance domain."""
from __future__ import annotations

import enum


class AttendanceEventType(str, enum.Enum):
    IN = "In"
    OUT = "Out"
    BREAK_OUT = "Break Out"
    BREAK_IN = "Break In"


class AttendanceSource(str, enum.Enum):
    BIOMETRIC = "Biometric"
    MANUAL = "Manual"
    MOCK = "Mock"


class AttendanceStatus(str, enum.Enum):
    """Attendance record statuses.

    Canonical priority order (highest → lowest):
        HOLIDAY > REST_DAY > ON_LEAVE > INCOMPLETE > HALF_DAY > LATE > UNDERTIME > OVERTIME > PRESENT

    Higher-priority statuses always win when multiple conditions apply.
    The AttendanceProcessor and AttendanceCalculationService both enforce
    this exact ordering — do not deviate.
    """
    PRESENT = "Present"
    LATE = "Late"
    ABSENT = "Absent"
    ON_LEAVE = "On Leave"
    REST_DAY = "Rest Day"
    HOLIDAY = "Holiday"
    HALF_DAY = "Half Day"
    INCOMPLETE = "Incomplete"
    UNDERTIME = "Undertime"
    OVERTIME = "Overtime"


class CorrectionType(str, enum.Enum):
    TIME_IN = "Time In"
    TIME_OUT = "Time Out"
    BREAK_OUT = "Break Out"
    BREAK_IN = "Break In"
    STATUS = "Status"


class CorrectionStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
