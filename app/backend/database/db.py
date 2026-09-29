"""
database/db.py — SQLAlchemy 2.x Engine, SessionLocal factory, Declarative Base, and get_db dependency.
"""

import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
try:
    from ..core.config import settings
except (ImportError, ValueError):
    from core.config import settings

logger = logging.getLogger("telemed.database")

# Declarative base for SQLAlchemy models
Base = declarative_base()

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}

# Test PostgreSQL connectivity if configured; fallback to local SQLite if unreachable
if db_url.startswith("postgresql"):
    try:
        pg_fast_url = db_url.replace("localhost", "127.0.0.1") if "localhost" in db_url else db_url
        test_engine = create_engine(pg_fast_url, connect_args={"connect_timeout": 10})
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        db_url = pg_fast_url
        logger.info("Connected to PostgreSQL database server successfully.")
    except Exception as e:
        is_prod = getattr(settings, "ENVIRONMENT", "").lower() == "production"
        if is_prod:
            raise RuntimeError(f"CRITICAL PRODUCTION DATABASE FAILURE: Configured PostgreSQL database is unreachable: {e}")
        sqlite_db_path = Path(__file__).resolve().parent.parent / "telemed_local.db"
        logger.warning(f"PostgreSQL server unreachable in development mode. Switching to local SQLite database ({sqlite_db_path}).")
        db_url = f"sqlite:///{sqlite_db_path}"
        connect_args = {"check_same_thread": False}


from sqlalchemy.pool import NullPool

engine_kwargs = {
    "echo": False,
    "pool_pre_ping": True,
    "connect_args": connect_args
}

if db_url.startswith("sqlite"):
    engine_kwargs["poolclass"] = NullPool
elif db_url.startswith("postgresql"):
    engine_kwargs.update({
        "pool_size": 30,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800
    })

engine = create_engine(db_url, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """Verify database connectivity at startup."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Database connection verified successfully ({engine.name}).")
        return True
    except Exception as e:
        logger.warning(f"Database connection test note: {str(e)}")
        return False


def create_tables() -> None:
    """Create all ORM database tables on the configured engine if they do not exist."""
    try:
        try:
            from ..models import models as pg_models
        except (ImportError, ValueError):
            from models import models as pg_models
    except Exception as e:
        logger.warning(f"Note loading models for create_tables: {e}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database ORM tables created/verified successfully.")


