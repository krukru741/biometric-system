"""Application service for Workforce operations."""
from __future__ import annotations

from typing import List, Optional

from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity, PositionEntity
from biometric_attendance.infrastructure.repositories.workforce_repository import (
    DepartmentRepository,
    EmployeeRepository,
    PositionRepository,
)


class WorkforceService:
    """Orchestrates business logic for Departments, Positions, and Employees."""

    def __init__(
        self,
        department_repository: DepartmentRepository,
        position_repository: PositionRepository,
        employee_repository: EmployeeRepository,
    ) -> None:
        self._dept_repo = department_repository
        self._pos_repo = position_repository
        self._emp_repo = employee_repository

    # ── Departments ──────────────────────────────────────────────────────────

    def get_all_departments(self) -> List[DepartmentEntity]:
        return self._dept_repo.get_all()

    def create_department(self, name: str, description: str, is_active: bool = True) -> DepartmentEntity:
        return self._dept_repo.create(name=name, description=description, is_active=is_active)

    # ── Positions ────────────────────────────────────────────────────────────

    def get_all_positions(self) -> List[PositionEntity]:
        return self._pos_repo.get_all()

    def create_position(
        self, name: str, description: str, department_id: Optional[int], is_active: bool = True
    ) -> PositionEntity:
        return self._pos_repo.create(
            name=name, description=description, department_id=department_id, is_active=is_active
        )

    # ── Employees ────────────────────────────────────────────────────────────

    def get_all_employees(self) -> List[EmployeeEntity]:
        return self._emp_repo.get_all()

    def create_employee(self, **kwargs) -> EmployeeEntity:
        """Create a new employee. 
        Accepts kwargs matching EmployeeModel fields.
        """
        # Validate required fields or apply business rules here if needed
        return self._emp_repo.create(**kwargs)
