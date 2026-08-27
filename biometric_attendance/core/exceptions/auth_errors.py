"""Domain exceptions for authentication and setup flows."""
from __future__ import annotations


class AuthError(Exception):
    """Base class for all authentication exceptions."""


class InvalidCredentialsError(AuthError):
    """Raised when username or password is incorrect."""

    def __init__(self) -> None:
        super().__init__("Invalid username or password.")


class AccountDisabledError(AuthError):
    """Raised when a valid user's account is deactivated."""

    def __init__(self, username: str) -> None:
        super().__init__(f"Account '{username}' is disabled.")
        self.username = username


class SetupAlreadyCompleteError(AuthError):
    """Raised when the setup wizard is called but users already exist."""

    def __init__(self) -> None:
        super().__init__("Setup is already complete. At least one user exists.")


class ValidationError(Exception):
    """Raised for invalid input during setup/creation flows."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field
        self.message = message
