"""Service interfaces for authentication and setup.

Application services implement these so ViewModels only depend
on the interface, not the concrete implementation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from biometric_attendance.core.dtos.auth_dtos import (
    CreateAdminRequest,
    LoginRequest,
    SessionUser,
)


class IAuthService(ABC):

    @abstractmethod
    def authenticate(self, request: LoginRequest) -> SessionUser:
        """Validate credentials and return a SessionUser.

        Raises:
            InvalidCredentialsError: if username/password do not match.
            AccountDisabledError: if the account is inactive.
        """
        ...


class ISetupService(ABC):

    @abstractmethod
    def is_first_run(self) -> bool:
        """Return True if no users exist yet (setup wizard must run)."""
        ...

    @abstractmethod
    def create_administrator(self, request: CreateAdminRequest) -> SessionUser:
        """Create the first admin user.

        Raises:
            SetupAlreadyCompleteError: if users already exist.
            ValidationError: if passwords don't match or fields are invalid.
        """
        ...
