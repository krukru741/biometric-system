"""DTOs for authentication flows.

These cross layer boundaries (core → application → app) carrying only
plain data — no ORM objects, no Qt types.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from biometric_attendance.core.enums.permissions import Permission
from biometric_attendance.core.enums.roles import RoleName


@dataclass(frozen=True)
class LoginRequest:
    """Data submitted from the login form."""

    username: str
    password: str  # plaintext — verified and discarded immediately


@dataclass(frozen=True)
class CreateAdminRequest:
    """Data submitted from the first-run setup wizard."""

    display_name: str
    username: str
    email: str
    password: str
    confirm_password: str


@dataclass(frozen=True)
class SessionUser:
    """Lightweight snapshot of the authenticated user stored in session.

    Safe to pass to ViewModels — no password hash exposed.
    """

    id: int
    username: str
    display_name: str
    email: str
    roles: frozenset[RoleName] = field(default_factory=frozenset)
    permissions: frozenset[Permission] = field(default_factory=frozenset)
    last_login_at: datetime | None = None

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions

    def has_role(self, role: RoleName) -> bool:
        return role in self.roles
