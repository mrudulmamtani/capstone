"""Shared FastAPI dependencies."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole


def get_current_user(
    db: Session = Depends(get_db),
    x_demo_role: str | None = Header(default=None, alias="X-Demo-Role"),
) -> User:
    try:
        role = UserRole((x_demo_role or UserRole.ADMIN.value).strip().lower())
    except ValueError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid demo role")

    user = db.execute(select(User).where(User.role == role, User.is_active.is_(True))).scalar_one_or_none()
    if user is None:
        user = User(
            id=f"demo-{role.value}",
            email=f"{role.value}@vision-sop.demo",
            full_name=f"Demo {role.value.title()}",
            hashed_password="demo-disabled",
            role=role,
            is_active=True,
        )
    return user


def require_role(*roles: UserRole):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return checker
