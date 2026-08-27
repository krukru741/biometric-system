"""Unit tests for AuthService.

Uses an in-memory SQLite DB via BIOMETRIC_DB_URL env override so
tests never touch the real database file.

Each test gets a *fresh* schema via function-scoped db_session fixture
so there is never any state leak between tests.
"""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("BIOMETRIC_DB_URL", "sqlite:///:memory:")

from biometric_attendance.infrastructure.data.database import engine, SessionFactory
from biometric_attendance.infrastructure.data.models import Base, seed_roles_and_permissions
from biometric_attendance.infrastructure.repositories.user_repository import UserRepository
from biometric_attendance.infrastructure.security.password_hasher import PasswordHasher
from biometric_attendance.application.services.auth_service import AuthService
from biometric_attendance.core.dtos.auth_dtos import LoginRequest, SessionUser
from biometric_attendance.core.enums.roles import RoleName
from biometric_attendance.core.enums.permissions import Permission
from biometric_attendance.core.exceptions.auth_errors import (
    AccountDisabledError,
    InvalidCredentialsError,
)


@pytest.fixture()
def db_session():
    """Fresh in-memory DB + schema for every single test (function scope)."""
    Base.metadata.create_all(bind=engine)
    session = SessionFactory()
    seed_roles_and_permissions(session)
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def repo(db_session):
    return UserRepository(session=db_session)


@pytest.fixture()
def hasher():
    return PasswordHasher()


@pytest.fixture()
def auth_service(repo, hasher):
    return AuthService(user_repository=repo, password_hasher=hasher)


@pytest.fixture()
def active_user(repo, hasher, db_session):
    """Create a real active user for testing."""
    user = repo.create(
        username="testuser",
        display_name="Test User",
        email="test@example.com",
        hashed_password=hasher.hash("correct_password"),
        role_names=[RoleName.HR.value],
    )
    db_session.commit()
    return user


class TestAuthService:

    def test_successful_login_returns_session_user(self, auth_service, active_user):
        result = auth_service.authenticate(
            LoginRequest(username="testuser", password="correct_password")
        )
        assert isinstance(result, SessionUser)
        assert result.username == "testuser"
        assert result.display_name == "Test User"

    def test_successful_login_loads_permissions(self, auth_service, active_user):
        result = auth_service.authenticate(
            LoginRequest(username="testuser", password="correct_password")
        )
        # HR role should have dashboard.view
        assert result.has_permission(Permission.DASHBOARD_VIEW)
        assert result.has_role(RoleName.HR)

    def test_wrong_password_raises_invalid_credentials(self, auth_service, active_user):
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate(
                LoginRequest(username="testuser", password="wrong_password")
            )

    def test_unknown_username_raises_invalid_credentials(self, auth_service):
        with pytest.raises(InvalidCredentialsError):
            auth_service.authenticate(
                LoginRequest(username="nonexistent", password="any_password")
            )

    def test_disabled_account_raises_account_disabled(
        self, auth_service, repo, hasher, db_session
    ):
        # Create a disabled user in this test's own fresh DB
        repo.create(
            username="disableduser",
            display_name="Disabled User",
            email="disabled@example.com",
            hashed_password=hasher.hash("password123"),
            role_names=[RoleName.KIOSK.value],
        )
        db_session.commit()

        # Disable them directly via ORM
        from biometric_attendance.infrastructure.data.models import UserModel
        model = db_session.query(UserModel).filter_by(username="disableduser").first()
        model.is_active = False
        db_session.commit()

        with pytest.raises(AccountDisabledError):
            auth_service.authenticate(
                LoginRequest(username="disableduser", password="password123")
            )

    def test_session_user_has_no_password(self, auth_service, active_user):
        """Ensure SessionUser does not expose hashed_password."""
        result = auth_service.authenticate(
            LoginRequest(username="testuser", password="correct_password")
        )
        assert not hasattr(result, "hashed_password"), "SessionUser must not expose password hash"
