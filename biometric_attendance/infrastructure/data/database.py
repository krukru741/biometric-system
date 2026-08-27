"""SQLAlchemy engine and session factory.

Usage (in repositories):
    with get_session() as session:
        session.add(model)
        session.commit()
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

# Allow override via environment variable for testing (e.g. SQLite :memory:)
_DB_URL = os.getenv(
    "BIOMETRIC_DB_URL",
    "sqlite:///biometric_attendance.db",
)

engine = create_engine(
    _DB_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


# Enable WAL mode for better SQLite concurrent read performance
@event.listens_for(engine, "connect")
def _set_wal_mode(dbapi_conn, _connection_record) -> None:  # type: ignore[type-arg]
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


SessionFactory: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional session scope."""
    session = SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
