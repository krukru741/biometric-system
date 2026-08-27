"""Authentication service implementation.

Validates credentials, stamps last_login_at, and returns a
lightweight SessionUser DTO for the UI layer. No PySide6/Qt imports.
"""
from __future__ import annotations

from biometric_attendance.core.dtos.auth_dtos import LoginRequest, SessionUser
from biometric_attendance.core.exceptions.auth_errors import (
    AccountDisabledError,
    InvalidCredentialsError,
)
from biometric_attendance.core.interfaces.i_auth_service import IAuthService
from biometric_attendance.core.interfaces.i_user_repository import IUserRepository
from biometric_attendance.infrastructure.security.password_hasher import PasswordHasher
from biometric_attendance.infrastructure.logging.logging_setup import get_logger

log = get_logger(__name__)


class AuthService(IAuthService):
    """Concrete authentication service.

    Wired by DI container — never instantiated directly in Views.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._repo = user_repository
        self._hasher = password_hasher

    def authenticate(self, request: LoginRequest) -> SessionUser:
        """Validate credentials and return a SessionUser.

        Raises:
            InvalidCredentialsError: username not found or password wrong.
            AccountDisabledError: account exists but is inactive.
        """
        log.info("auth.attempt", username=request.username)

        user = self._repo.get_by_username(request.username)

        # Use constant-time comparison to avoid timing attacks
        if user is None or not self._hasher.verify(request.password, user.hashed_password):
            log.warning("auth.failed", username=request.username)
            raise InvalidCredentialsError()

        if not user.is_active:
            log.warning("auth.disabled", username=request.username)
            raise AccountDisabledError(user.username)

        # Stamp last login time
        self._repo.update_last_login(user.id)

        log.info("auth.success", username=user.username, user_id=user.id)

        return SessionUser(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            roles=user.roles,
            permissions=user.permissions,
        )
