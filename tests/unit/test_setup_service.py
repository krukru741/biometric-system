"""Unit tests for SetupService."""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("BIOMETRIC_DB_URL", "sqlite:///:memory:")

from biometric_attendance.infrastructure.data.database import engine, SessionFactory
from biometric_attendance.infrastructure.data.models import Base, seed_roles_and_permissions
from biometric_attendance.infrastructure.repositories.user_repository import UserRepository
from biometric_attendance.infrastructure.security.password_hasher import PasswordHasher
from biometric_attendance.application.services.setup_service import SetupService
from biometric_attendance.core.dtos.auth_dtos import CreateAdminRequest, SessionUser
from biometric_attendance.core.enums.permissions import Permission
from biometric_attendance.core.enums.roles import RoleName
from biometric_attendance.core.exceptions.auth_errors import (
    SetupAlreadyCompleteError,
    ValidationError,
)


@pytest.fixture()
def fresh_db():
    """Fresh in-memory DB for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionFactory()
    seed_roles_and_permissions(session)
    session.commit()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def setup_service(fresh_db):
    repo = UserRepository(session=fresh_db)
    hasher = PasswordHasher()
    return SetupService(user_repository=repo, password_hasher=hasher), fresh_db


class TestSetupService:

    def test_is_first_run_on_empty_db(self, setup_service):
        svc, _ = setup_service
        assert svc.is_first_run() is True

    def test_create_admin_returns_session_user(self, setup_service):
        svc, db = setup_service
        result = svc.create_administrator(
            CreateAdminRequest(
                display_name="System Admin",
                username="admin",
                email="admin@company.com",
                password="SecurePass1!",
                confirm_password="SecurePass1!",
            )
        )
        db.commit()
        assert isinstance(result, SessionUser)
        assert result.username == "admin"
        assert result.has_role(RoleName.ADMINISTRATOR)
        assert result.has_permission(Permission.USERS_MANAGE)

    def test_create_admin_not_first_run_afterwards(self, setup_service):
        svc, db = setup_service
        svc.create_administrator(
            CreateAdminRequest(
                display_name="Admin",
                username="admin2",
                email="admin2@company.com",
                password="Pass1234!",
                confirm_password="Pass1234!",
            )
        )
        db.commit()
        assert svc.is_first_run() is False

    def test_second_admin_raises_setup_complete(self, setup_service):
        svc, db = setup_service
        svc.create_administrator(
            CreateAdminRequest(
                display_name="Admin",
                username="admin3",
                email="admin3@company.com",
                password="Pass1234!",
                confirm_password="Pass1234!",
            )
        )
        db.commit()
        with pytest.raises(SetupAlreadyCompleteError):
            svc.create_administrator(
                CreateAdminRequest(
                    display_name="Admin2",
                    username="admin4",
                    email="admin4@company.com",
                    password="Pass1234!",
                    confirm_password="Pass1234!",
                )
            )

    def test_password_mismatch_raises_validation_error(self, setup_service):
        svc, _ = setup_service
        with pytest.raises(ValidationError) as exc_info:
            svc.create_administrator(
                CreateAdminRequest(
                    display_name="Admin",
                    username="admin5",
                    email="admin5@company.com",
                    password="Pass1234!",
                    confirm_password="Different!",
                )
            )
        assert exc_info.value.field == "confirm_password"

    def test_short_password_raises_validation_error(self, setup_service):
        svc, _ = setup_service
        with pytest.raises(ValidationError) as exc_info:
            svc.create_administrator(
                CreateAdminRequest(
                    display_name="Admin",
                    username="admin6",
                    email="admin6@company.com",
                    password="short",
                    confirm_password="short",
                )
            )
        assert exc_info.value.field == "password"

    def test_empty_username_raises_validation_error(self, setup_service):
        svc, _ = setup_service
        with pytest.raises(ValidationError) as exc_info:
            svc.create_administrator(
                CreateAdminRequest(
                    display_name="Admin",
                    username="",
                    email="admin7@company.com",
                    password="Pass1234!",
                    confirm_password="Pass1234!",
                )
            )
        assert exc_info.value.field == "username"

    def test_invalid_email_raises_validation_error(self, setup_service):
        svc, _ = setup_service
        with pytest.raises(ValidationError) as exc_info:
            svc.create_administrator(
                CreateAdminRequest(
                    display_name="Admin",
                    username="admin8",
                    email="not-an-email",
                    password="Pass1234!",
                    confirm_password="Pass1234!",
                )
            )
        assert exc_info.value.field == "email"
