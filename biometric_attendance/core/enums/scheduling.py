"""Enums for the Scheduling domain."""
from __future__ import annotations

import enum


class HolidayType(str, enum.Enum):
    REGULAR = "Regular Holiday"
    SPECIAL = "Special Non-Working Holiday"
    COMPANY = "Company Holiday"


class ScheduleStatus(str, enum.Enum):
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
