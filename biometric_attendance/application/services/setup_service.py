"""First-run setup service.

Detects empty users table and creates the initial Administrator account.
Called once during app startup routing logic — never used again after
the first user exists.
"""
from __future__ import annotations

from biometric_attendance.core.dtos.auth_dtos import CreateAdminRequest, SessionUser
from biometric_attendance.core.enums.roles import RoleName
from biometric_attendance.core.exceptions.auth_errors import (
    SetupAlreadyCompleteError,
    ValidationError,
)
from biometric_attendance.core.interfaces.i_auth_service import ISetupService
from biometric_attendance.core.interfaces.i_user_repository import IUserRepository
from biometric_attendance.infrastructure.security.password_hasher import PasswordHasher
from biometric_attendance.infrastructure.logging.logging_setup import get_logger

log = get_logger(__name__)

_MIN_PASSWORD_LENGTH = 8


class SetupService(ISetupService):
    """Handles first-run administrator account creation."""

    def __init__(
        self,
        user_repository: IUserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._repo = user_repository
        self._hasher = password_hasher

    def is_first_run(self) -> bool:
        """Return True if no users exist yet."""
        return self._repo.count() == 0

    def create_administrator(self, request: CreateAdminRequest) -> SessionUser:
        """Create the first admin account.

        Raises:
            SetupAlreadyCompleteError: if users already exist.
            ValidationError: for any invalid field.
        """
        if not self.is_first_run():
            raise SetupAlreadyCompleteError()

        # ── Validation ────────────────────────────────────────────────────────
        if not request.display_name.strip():
            raise ValidationError("display_name", "Display name is required.")

        if not request.username.strip():
            raise ValidationError("username", "Username is required.")

        if len(request.username.strip()) < 3:
            raise ValidationError("username", "Username must be at least 3 characters.")

        if not request.email.strip() or "@" not in request.email:
            raise ValidationError("email", "A valid email address is required.")

        if len(request.password) < _MIN_PASSWORD_LENGTH:
            raise ValidationError(
                "password",
                f"Password must be at least {_MIN_PASSWORD_LENGTH} characters.",
            )

        if request.password != request.confirm_password:
            raise ValidationError("confirm_password", "Passwords do not match.")

        # ── Create user ───────────────────────────────────────────────────────
        hashed = self._hasher.hash(request.password)

        user = self._repo.create(
            username=request.username.strip(),
            display_name=request.display_name.strip(),
            email=request.email.strip().lower(),
            hashed_password=hashed,
            role_names=[RoleName.ADMINISTRATOR.value],
        )

        log.info(
            "setup.admin_created",
            username=user.username,
            user_id=user.id,
        )

        return SessionUser(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            roles=user.roles,
            permissions=user.permissions,
        )
