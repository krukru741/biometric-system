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
    pool_pre_ping=True,
    echo=False,
)

import logging
logging.basicConfig()
logger = logging.getLogger("sqlalchemy.pool")
logger.setLevel(logging.INFO)

@event.listens_for(engine, "checkout")
def checkout_listener(dbapi_conn, connection_rec, connection_proxy):
    logger.info("Connection checked out from pool")

@event.listens_for(engine, "checkin")
def checkin_listener(dbapi_conn, connection_rec):
    logger.info("Connection returned to pool")


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


import os
import time
import traceback
import logging

db_logger = logging.getLogger("biometric_attendance.database")
_active_sessions = {}

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionFactory()
    session_id = id(session)
    start_time = time.time()
    caller = traceback.extract_stack()[-3]
    loc = f"{os.path.basename(caller.filename)}:{caller.lineno}"
    _active_sessions[session_id] = (start_time, loc)
    
    db_logger.debug(f"Entered get_session from {loc}")
    # print(f"DEBUG: get_session opened from {loc}")
    
    # Check for long-running sessions
    for sid, (st, sloc) in list(_active_sessions.items()):
        elapsed = time.time() - st
        if elapsed > 5:
            msg = f"LEAK DETECTED: Session {sid} opened at {sloc} has been open for {elapsed:.2f} seconds!"
            db_logger.warning(msg)
            print(msg)

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        _active_sessions.pop(session_id, None)

@contextmanager
def auto_session(session: Session | None = None) -> Generator[Session, None, None]:
    """
    Yields the provided session if it exists, otherwise opens a new 
    short-lived session using get_session().
    """
    if session is not None:
        yield session
    else:
        with get_session() as s:
            yield s
