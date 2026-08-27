"""Concrete SQLAlchemy implementation of IUserRepository."""
from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from biometric_attendance.core.entities.user import UserEntity
from biometric_attendance.core.enums.permissions import Permission
from biometric_attendance.core.enums.roles import RoleName
from biometric_attendance.core.interfaces.i_user_repository import IUserRepository
from biometric_attendance.infrastructure.data.models import RoleModel, UserModel


class UserRepository(IUserRepository):
    """Reads/writes User aggregates via SQLAlchemy sessions."""

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _to_entity(self, model: UserModel) -> UserEntity:
        """Map ORM model → domain entity, resolving roles + permissions."""
        roles: set[RoleName] = set()
        permissions: set[Permission] = set()

        for role_model in model.roles:
            try:
                roles.add(RoleName(role_model.name))
            except ValueError:
                pass  # Unknown role name — skip
            for perm_model in role_model.permissions:
                try:
                    permissions.add(Permission(perm_model.name))
                except ValueError:
                    pass  # Unknown permission — skip

        return UserEntity(
            id=model.id,
            username=model.username,
            display_name=model.display_name,
            email=model.email,
            is_active=model.is_active,
            hashed_password=model.hashed_password,
            roles=frozenset(roles),
            permissions=frozenset(permissions),
            last_login_at=model.last_login_at,
            created_at=model.created_at,
        )

    # ── IUserRepository ───────────────────────────────────────────────────────

    def count(self) -> int:
        return self._session.query(UserModel).count()

    def get_by_username(self, username: str) -> UserEntity | None:
        model = (
            self._session.query(UserModel)
            .filter(UserModel.username == username)
            .first()
        )
        return self._to_entity(model) if model else None

    def get_by_id(self, user_id: int) -> UserEntity | None:
        model = self._session.get(UserModel, user_id)
        return self._to_entity(model) if model else None

    def create(
        self,
        username: str,
        display_name: str,
        email: str,
        hashed_password: str,
        role_names: list[str],
    ) -> UserEntity:
        # Resolve role models
        role_models: list[RoleModel] = []
        for role_name in role_names:
            role = self._session.query(RoleModel).filter_by(name=role_name).first()
            if role is None:
                raise ValueError(f"Role not found: {role_name}")
            role_models.append(role)

        user = UserModel(
            username=username,
            display_name=display_name,
            email=email,
            hashed_password=hashed_password,
            is_active=True,
        )
        user.roles = role_models
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return self._to_entity(user)

    def update_last_login(self, user_id: int) -> None:
        model = self._session.get(UserModel, user_id)
        if model:
            model.last_login_at = datetime.datetime.now()
            self._session.commit()
