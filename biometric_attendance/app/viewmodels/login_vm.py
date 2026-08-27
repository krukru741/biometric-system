"""LoginViewModel — bridges LoginView and AuthService.

Rules (from 17-PYTHON-PROJECT-STRUCTURE.md):
- No direct DB or service instantiation here.
- Receives IAuthService via DI constructor injection.
- Exposes state as Signals, commands as Slots.
- Never imports any Qt widget class.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from biometric_attendance.core.dtos.auth_dtos import LoginRequest, SessionUser
from biometric_attendance.core.exceptions.auth_errors import (
    AccountDisabledError,
    AuthError,
    InvalidCredentialsError,
)
from biometric_attendance.core.interfaces.i_auth_service import IAuthService
from biometric_attendance.infrastructure.logging.logging_setup import get_logger

log = get_logger(__name__)


class LoginViewModel(QObject):
    """ViewModel for the login screen.

    Signals:
        login_success(SessionUser): emitted when authentication succeeds.
        login_failed(str):          emitted with a user-facing error message.
        loading_changed(bool):      emitted to toggle loading indicator.
    """

    login_success = Signal(object)   # SessionUser
    login_failed = Signal(str)
    loading_changed = Signal(bool)

    def __init__(self, auth_service: IAuthService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._auth_service = auth_service

    @Slot(str, str)
    def login(self, username: str, password: str) -> None:
        """Called by LoginView when the Sign In button is clicked."""
        username = username.strip()

        if not username:
            self.login_failed.emit("Please enter your username.")
            return
        if not password:
            self.login_failed.emit("Please enter your password.")
            return

        self.loading_changed.emit(True)
        try:
            session_user = self._auth_service.authenticate(
                LoginRequest(username=username, password=password)
            )
            self.login_success.emit(session_user)
        except InvalidCredentialsError:
            self.login_failed.emit("Incorrect username or password. Please try again.")
        except AccountDisabledError:
            self.login_failed.emit(
                "Your account has been disabled. Please contact your administrator."
            )
        except Exception as exc:
            log.exception("login.unexpected_error", error=str(exc))
            self.login_failed.emit("An unexpected error occurred. Please try again.")
        finally:
            self.loading_changed.emit(False)
