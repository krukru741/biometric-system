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
        session=db_session,
    )

    department_repository = providers.Factory(
        DepartmentRepository,
        session=db_session,
    )

    position_repository = providers.Factory(
        PositionRepository,
        session=db_session,
    )

    employee_repository = providers.Factory(
        EmployeeRepository,
        session=db_session,
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
