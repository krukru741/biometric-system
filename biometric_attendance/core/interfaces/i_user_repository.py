"""Repository interface for User aggregate.

All methods the application layer needs from user storage.
Infrastructure implements this; application only imports the interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from biometric_attendance.core.entities.user import UserEntity


class IUserRepository(ABC):

    @abstractmethod
    def count(self) -> int:
        """Return total number of user records (used for first-run detection)."""
        ...

    @abstractmethod
    def get_by_username(self, username: str) -> UserEntity | None:
        """Return user entity with roles/permissions loaded, or None."""
        ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> UserEntity | None:
        ...

    @abstractmethod
    def create(
        self,
        username: str,
        display_name: str,
        email: str,
        hashed_password: str,
        role_names: list[str],
    ) -> UserEntity:
        """Persist a new user and assign given roles. Returns the saved entity."""
        ...

    @abstractmethod
    def update_last_login(self, user_id: int) -> None:
        """Stamp last_login_at = now() for the given user."""
        ...
