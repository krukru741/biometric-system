"""SetupWizardViewModel — drives the first-run administrator creation screen."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from biometric_attendance.core.dtos.auth_dtos import CreateAdminRequest, SessionUser
from biometric_attendance.core.exceptions.auth_errors import (
    SetupAlreadyCompleteError,
    ValidationError,
)
from biometric_attendance.core.interfaces.i_auth_service import ISetupService
from biometric_attendance.infrastructure.logging.logging_setup import get_logger

log = get_logger(__name__)


class SetupWizardViewModel(QObject):
    """ViewModel for the first-run setup wizard.

    Signals:
        setup_success(SessionUser): emitted after the admin account is created.
        field_error(str, str):      emitted with (field_name, error_message).
        general_error(str):         emitted for non-field-specific errors.
        loading_changed(bool):      toggle loading / disable button.
    """

    setup_success = Signal(object)    # SessionUser
    field_error = Signal(str, str)    # (field_name, message)
    general_error = Signal(str)
    loading_changed = Signal(bool)

    def __init__(self, setup_service: ISetupService, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._setup_service = setup_service

    @Slot(str, str, str, str, str)
    def create_admin(
        self,
        display_name: str,
        username: str,
        email: str,
        password: str,
        confirm_password: str,
    ) -> None:
        """Called when the user clicks 'Create Account' in the wizard."""
        self.loading_changed.emit(True)
        try:
            session_user = self._setup_service.create_administrator(
                CreateAdminRequest(
                    display_name=display_name,
                    username=username,
                    email=email,
                    password=password,
                    confirm_password=confirm_password,
                )
            )
            self.setup_success.emit(session_user)
        except ValidationError as exc:
            self.field_error.emit(exc.field, exc.message)
        except SetupAlreadyCompleteError:
            self.general_error.emit("Setup is already complete.")
        except Exception as exc:
            log.exception("setup.unexpected_error", error=str(exc))
            self.general_error.emit("An unexpected error occurred. Please try again.")
        finally:
            self.loading_changed.emit(False)
