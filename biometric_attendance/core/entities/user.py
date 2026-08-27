"""Domain entities for User, Role, and Permission.

These are pure dataclasses — no SQLAlchemy, no PySide6.
They represent the business concepts used by application services.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from biometric_attendance.core.enums.permissions import Permission
from biometric_attendance.core.enums.roles import RoleName


@dataclass(frozen=True)
class PermissionEntity:
    id: int
    name: Permission
    description: str = ""


@dataclass(frozen=True)
class RoleEntity:
    id: int
    name: RoleName
    description: str = ""
    permissions: frozenset[Permission] = field(default_factory=frozenset)


@dataclass(frozen=True)
class UserEntity:
    """Read-only snapshot of a user loaded from the DB.

    Never stored with a plaintext password — hashed_password is the
    bcrypt hash kept only in the infrastructure layer.
    """

    id: int
    username: str
    display_name: str
    email: str
    is_active: bool
    hashed_password: str  # kept for auth verification only, never exposed in UI
    roles: frozenset[RoleName] = field(default_factory=frozenset)
    permissions: frozenset[Permission] = field(default_factory=frozenset)
    last_login_at: datetime | None = None
    created_at: datetime | None = None

    def has_permission(self, perm: Permission) -> bool:
        """Return True if this user holds the given permission."""
        return perm in self.permissions

    def has_role(self, role: RoleName) -> bool:
        """Return True if this user holds the given role."""
        return role in self.roles
