"""Dependency Injection container (dependency-injector).

All wiring is declared here. Views/ViewModels receive their
dependencies through constructor injection — never via global state.

Usage:
    container = AppContainer()
    container.wire(modules=[...])
"""
from __future__ import annotations

from dependency_injector import containers, providers

from biometric_attendance.infrastructure.data.database import SessionFactory
from biometric_attendance.infrastructure.repositories.user_repository import UserRepository
from biometric_attendance.infrastructure.security.password_hasher import PasswordHasher
from biometric_attendance.application.services.auth_service import AuthService
from biometric_attendance.application.services.setup_service import SetupService
from biometric_attendance.application.services.workforce_service import WorkforceService

from biometric_attendance.infrastructure.repositories.scheduling_repository import (
    ShiftTemplateRepository,
    HolidayRepository,
    EmployeeScheduleRepository,
)
from biometric_attendance.application.services.scheduling_service import SchedulingService
from biometric_attendance.infrastructure.repositories.workforce_repository import (
    DepartmentRepository,
    EmployeeRepository,
    PositionRepository,
)


class AppContainer(containers.DeclarativeContainer):
    """Application-level DI container."""

    # ── Infrastructure ────────────────────────────────────────────────────────

    db_session = providers.Factory(SessionFactory)

    password_hasher = providers.Singleton(PasswordHasher)

    user_repository = providers.Factory(
        UserRepository,
    )

    department_repository = providers.Factory(
        DepartmentRepository,
    )

    position_repository = providers.Factory(
        PositionRepository,
    )

    employee_repository = providers.Factory(
        EmployeeRepository,
    )

    # ── Application Services ─────────────────────────────────────────────────

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        password_hasher=password_hasher,
    )

    setup_service = providers.Factory(
        SetupService,
        user_repository=user_repository,
        password_hasher=password_hasher,
    )

    workforce_service = providers.Factory(
        WorkforceService,
        department_repository=department_repository,
        position_repository=position_repository,
        employee_repository=employee_repository,
    )


    # ── Scheduling ────────────────────────────────────────────────────────
    
    shift_template_repository = providers.Factory(
        ShiftTemplateRepository,
    )
    
    holiday_repository = providers.Factory(
        HolidayRepository,
    )
    
    employee_schedule_repository = providers.Factory(
        EmployeeScheduleRepository,
    )
    
    scheduling_service = providers.Factory(
        SchedulingService,
        shift_template_repository=shift_template_repository,
        holiday_repository=holiday_repository,
        employee_schedule_repository=employee_schedule_repository,
        employee_repository=employee_repository,
        department_repository=department_repository,
    )

    # ── Attendance ────────────────────────────────────────────────────────────

    attendance_event_repository = providers.Factory(
        "biometric_attendance.infrastructure.repositories.attendance_repository.AttendanceEventRepository",
    )

    attendance_record_repository = providers.Factory(
        "biometric_attendance.infrastructure.repositories.attendance_repository.AttendanceRecordRepository",
    )

    attendance_correction_repository = providers.Factory(
        "biometric_attendance.infrastructure.repositories.attendance_repository.AttendanceCorrectionRepository",
    )

    schedule_resolver = providers.Factory(
        "biometric_attendance.application.attendance.schedule_resolver.ScheduleResolver",
        schedule_repository=employee_schedule_repository,
        shift_repository=shift_template_repository,
        holiday_repository=holiday_repository,
    )

    calculation_service = providers.Factory(
        "biometric_attendance.application.attendance.calculation_service.AttendanceCalculationService",
    )

    attendance_processor = providers.Factory(
        "biometric_attendance.application.attendance.attendance_processor.AttendanceProcessor",
        event_repository=attendance_event_repository,
        record_repository=attendance_record_repository,
        employee_repository=employee_repository,
        schedule_resolver=schedule_resolver,
        calculation_service=calculation_service,
    )

    attendance_event_service = providers.Factory(
        "biometric_attendance.application.attendance.event_service.AttendanceEventService",
        event_repository=attendance_event_repository,
        processor=attendance_processor,
    )

    attendance_correction_service = providers.Factory(
        "biometric_attendance.application.attendance.correction_service.AttendanceCorrectionService",
        correction_repository=attendance_correction_repository,
        record_repository=attendance_record_repository,
        employee_repository=employee_repository,
        schedule_resolver=schedule_resolver,
        calculation_service=calculation_service,
    )

    # ── Biometrics ────────────────────────────────────────────────────────────

    employee_biometric_repository = providers.Factory(
        "biometric_attendance.infrastructure.repositories.biometric_repository.EmployeeBiometricRepository",
    )

    biometric_device_repository = providers.Factory(
        "biometric_attendance.infrastructure.repositories.biometric_repository.BiometricDeviceRepository",
    )

    biometric_log_repository = providers.Factory(
        "biometric_attendance.infrastructure.repositories.biometric_repository.BiometricLogRepository",
    )

    encryption_service = providers.Singleton(
        "biometric_attendance.application.biometrics.encryption_service.BiometricEncryptionService",
    )

    biometric_enrollment_service = providers.Factory(
        "biometric_attendance.application.biometrics.enrollment_service.BiometricEnrollmentService",
        repository=employee_biometric_repository,
        encryption_service=encryption_service,
    )

    # Note: adapter factory just returns a Mock adapter
    mock_adapter_factory = providers.Callable(
        lambda e_strs: __import__("biometric_attendance.infrastructure.adapters.mock_biometric_adapter").infrastructure.adapters.mock_biometric_adapter.MockBiometricAdapter(e_strs)
    )

    biometric_device_service = providers.Factory(
        "biometric_attendance.application.biometrics.device_service.BiometricDeviceService",
        device_repo=biometric_device_repository,
        log_repo=biometric_log_repository,
        # A simple lambda that ignores device_entity and just creates a mock adapter. 
        adapter_factory=providers.Callable(
            lambda *args: __import__("biometric_attendance.infrastructure.adapters.mock_biometric_adapter", fromlist=["MockBiometricAdapter"]).MockBiometricAdapter([])
        ),
    )

    biometric_sync_service = providers.Factory(
        "biometric_attendance.application.biometrics.sync_service.BiometricSyncService",
        device_repo=biometric_device_repository,
        log_repo=biometric_log_repository,
        employee_repo=employee_repository,
        biometric_repo=employee_biometric_repository,
        attendance_event_svc=attendance_event_service,
        encryption_service=encryption_service,
        # The adapter factory for sync needs the list of active employee ID strings to generate mock events
        adapter_factory=providers.Callable(
            lambda *args: __import__("biometric_attendance.infrastructure.adapters.mock_biometric_adapter", fromlist=["MockBiometricAdapter"]).MockBiometricAdapter(
                # we'll inject employee_strs in the VM when we pull logs, or we can just mock it here
                []
            )
        )
    )
