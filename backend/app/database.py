"""Database engine/session setup (PostgreSQL by default, SQLite fallback)."""

from __future__ import annotations

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

settings = get_settings()

_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, echo=False, connect_args=_connect_args)


def init_db() -> None:
    """Create all tables. In production, prefer real migrations (Alembic);
    for this prototype, declarative create_all keeps setup single-command."""
    from app import models  # noqa: F401  (ensure models are registered)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
