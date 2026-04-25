"""Pytest fixtures.

Uses an in-memory SQLite database so the suite runs without Postgres. A few
SQLAlchemy types have dialect-specific defaults (JSONB, etc.) that we swap at
compile-time for SQLite.
"""
from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("LLM_PROVIDER", "stub")

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.session import Base  # noqa: E402


@pytest.fixture(scope="session")
def settings():
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture()
def db(settings):
    engine = create_engine(settings.database_url, future=True)

    # SQLite doesn't support JSONB — fall back to plain JSON for tests.
    for t in Base.metadata.tables.values():
        for c in t.columns:
            if c.type.__class__.__name__ == "JSONB":
                from sqlalchemy import JSON

                c.type = JSON()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sess = Session()
    try:
        yield sess
    finally:
        sess.close()
        Base.metadata.drop_all(engine)
