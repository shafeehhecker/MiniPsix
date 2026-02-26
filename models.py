"""
Database models for Mini-P6 using SQLAlchemy + SQLite.
"""
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ActivityRecord(Base):
    """Persistent storage for an Activity."""
    __tablename__ = "activities"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    duration = Column(Integer, nullable=False, default=0)
    predecessors = Column(String, default="")   # comma-separated IDs

    # CPM results (cached after last schedule run)
    ES = Column(Integer, default=0)
    EF = Column(Integer, default=0)
    LS = Column(Integer, default=0)
    LF = Column(Integer, default=0)
    total_float = Column(Integer, default=0)
    is_critical = Column(Boolean, default=False)
