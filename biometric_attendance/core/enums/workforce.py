"""Enums for the Workforce domain."""
from __future__ import annotations

import enum


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    ARCHIVED = "Archived"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "Full-Time"
    PART_TIME = "Part-Time"
    CONTRACT = "Contract"
