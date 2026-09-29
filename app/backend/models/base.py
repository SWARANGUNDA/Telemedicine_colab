"""
models/base.py — Base model class importing SQLAlchemy Declarative Base.
"""

try:
    from ..database.db import Base
except (ImportError, ValueError):
    from database.db import Base

__all__ = ["Base"]
