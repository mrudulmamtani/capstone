"""User accounts (operators, supervisors, admins)."""
from __future__ import annotations

import enum

from sqlalchemy import Enum as SAEnum
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKey


class UserRole(str, enum.Enum):
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    ENGINEER = "engineer"
    ADMIN = "admin"


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", create_type=False, values_callable=lambda e: [m.value for m in e]),
        default=UserRole.OPERATOR, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User {self.email} role={self.role}>"
