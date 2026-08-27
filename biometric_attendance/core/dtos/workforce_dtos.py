"""DTOs for the Workforce domain (Departments, Positions, Employees)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from biometric_attendance.core.enums.workforce import EmploymentStatus, EmploymentType


@dataclass(frozen=True)
class DepartmentEntity:
    id: int
    name: str
    description: str
    is_active: bool


@dataclass(frozen=True)
class PositionEntity:
    id: int
    name: str
    description: str
    department_id: Optional[int]
    is_active: bool
    department_name: Optional[str] = None


@dataclass(frozen=True)
class EmployeeEntity:
    """Read-only entity for Employee."""
    id: int
    
    # Personal
    employee_id: str
    first_name: str
    middle_name: str
    last_name: str
    suffix: str
    birth_date: Optional[date]
    gender: str
    phone: str
    email: str
    address: str
    photo_path: Optional[str]
    
    # Employment
    department_id: Optional[int]
    department_name: Optional[str]
    position_id: Optional[int]
    position_name: Optional[str]
    employment_type: EmploymentType
    date_hired: Optional[date]
    status: EmploymentStatus
    supervisor_id: Optional[int]
    
    # Attendance config
    grace_period_mins: int
    overtime_eligible: bool
    rest_day: str
    
    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return " ".join(parts)
