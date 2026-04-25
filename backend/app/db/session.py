"""SQLAlchemy engine + session factory.

Uses the synchronous driver for the main app (simpler reasoning for CV-heavy
workloads) with an async variant available for future WebSocket scale-up.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """Declarative base — all ORM models inherit from this."""


# ``future=True`` isn't needed in SQLAlchemy 2.x (already default) but kept
# here to be explicit for readers migrating from 1.4.
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if make_url(settings.database_url).get_backend_name() != "sqlite":
    engine_kwargs.update(
        pool_size=settings.database_pool_size,
        max_overflow=5,
    )

engine = create_engine(settings.database_url, **engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: yield a DB session and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
