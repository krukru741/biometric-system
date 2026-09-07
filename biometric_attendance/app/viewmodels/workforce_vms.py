"""ViewModels for Workforce management (Departments, Positions, Employees)."""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Slot

from biometric_attendance.application.services.workforce_service import WorkforceService
from biometric_attendance.core.dtos.workforce_dtos import DepartmentEntity, EmployeeEntity, PositionEntity


class DepartmentsViewModel(QObject):
    error_occurred = Signal(str)
    departments_loaded = Signal(list)  # list[DepartmentEntity]

    def __init__(self, workforce_service: WorkforceService):
        super().__init__()
        self._service = workforce_service

    @Slot()
    def load_departments(self) -> None:
        try:
            depts = self._service.get_all_departments()
            self.departments_loaded.emit(depts)
        except Exception as e:
            self.error_occurred.emit(str(e))

    @Slot(str, str)
    def create_department(self, name: str, description: str) -> None:
        try:
            self._service.create_department(name=name, description=description)
            self.load_departments()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def update_department(self, id: int, name: str, description: str) -> None:
        try:
            self._service.update_department(id=id, name=name, description=description)
            self.load_departments()
        except Exception as e:
            self.error_occurred.emit(str(e))


class PositionsViewModel(QObject):
    error_occurred = Signal(str)
    positions_loaded = Signal(list)  # list[PositionEntity]
    departments_loaded = Signal(list)  # list[DepartmentEntity] for combobox

    def __init__(self, workforce_service: WorkforceService):
        super().__init__()
        self._service = workforce_service

    @Slot()
    def load_data(self) -> None:
        try:
            depts = self._service.get_all_departments()
            self.departments_loaded.emit(depts)

            positions = self._service.get_all_positions()
            self.positions_loaded.emit(positions)
        except Exception as e:
            self.error_occurred.emit(str(e))

    @Slot(str, str, int)
    def create_position(self, name: str, description: str, department_id: int) -> None:
        try:
            dept_id = department_id if department_id > 0 else None
            self._service.create_position(name=name, description=description, department_id=dept_id)
            self.load_data()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def update_position(self, id: int, name: str, description: str, department_id: int) -> None:
        try:
            dept_id = department_id if department_id > 0 else None
            self._service.update_position(id=id, name=name, description=description, department_id=dept_id)
            self.load_data()
        except Exception as e:
            self.error_occurred.emit(str(e))


class EmployeesViewModel(QObject):
    loading_changed = Signal(bool)
    error_occurred = Signal(str)
    employees_loaded = Signal(list)
    departments_loaded = Signal(list)
    positions_loaded = Signal(list)

    def __init__(self, workforce_service: WorkforceService):
        super().__init__()
        from biometric_attendance.app.viewmodels.async_loader import AsyncLoader
        self._service = workforce_service
        self._loader = AsyncLoader(self, error_message="Unable to load employees. Please try again.")
        self._loader.busy_changed.connect(self.loading_changed)
        self._loader.loaded.connect(self._on_loaded)
        self._loader.failed.connect(self.error_occurred)

    @Slot()
    def load_data(self) -> None:
        def read():
            return (self._service.get_all_departments(), self._service.get_all_positions(), self._service.get_all_employees())
        self._loader.load(read)

    @Slot(object)
    def _on_loaded(self, result):
        departments, positions, employees = result
        self.departments_loaded.emit(departments)
        self.positions_loaded.emit(positions)
        self.employees_loaded.emit(employees)

    def create_employee(self, data: dict) -> None:
        """Create an employee from a dictionary of fields."""
        try:
            self._service.create_employee(**data)
            self.load_data()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def update_employee(self, id: int, data: dict) -> None:
        """Update an existing employee from a dictionary of fields."""
        try:
            self._service.update_employee(id=id, **data)
            self.load_data()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def archive_employee(self, id: int) -> None:
        """Set an employee status to ARCHIVED."""
        try:
            self._service.archive_employee(id=id)
            self.load_data()
        except Exception as e:
            self.error_occurred.emit(str(e))
