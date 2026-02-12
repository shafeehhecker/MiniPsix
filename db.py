"""
Database access layer for Mini-P6.
Provides simple CRUD operations for Activity records.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Dict, Optional

from .models import Base, ActivityRecord
from engine.activity import Activity


_engine = None
_SessionLocal = None


def init_db(db_path: str = "mini_p6.db"):
    """Initialize the database (create tables if needed)."""
    global _engine, _SessionLocal
    _engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(_engine)
    _SessionLocal = sessionmaker(bind=_engine)


def get_session() -> Session:
    if _SessionLocal is None:
        init_db()
    return _SessionLocal()


# ------------------------------------------------------------------
# CRUD helpers
# ------------------------------------------------------------------

def load_all_activities() -> Dict[str, Activity]:
    """Load all activities from DB and return as {id: Activity} dict."""
    with get_session() as session:
        records = session.query(ActivityRecord).all()
        return {r.id: _record_to_activity(r) for r in records}


def save_activity(activity: Activity):
    """Insert or update a single activity."""
    with get_session() as session:
        existing = session.get(ActivityRecord, activity.id)
        if existing:
            _update_record(existing, activity)
        else:
            session.add(_activity_to_record(activity))
        session.commit()


def save_all_activities(activities: Dict[str, Activity]):
    """Bulk save / update all activities (used after CPM run)."""
    with get_session() as session:
        for act in activities.values():
            existing = session.get(ActivityRecord, act.id)
            if existing:
                _update_record(existing, act)
            else:
                session.add(_activity_to_record(act))
        session.commit()


def delete_activity(activity_id: str):
    """Remove an activity from the database."""
    with get_session() as session:
        record = session.get(ActivityRecord, activity_id)
        if record:
            session.delete(record)
            session.commit()


def activity_id_exists(activity_id: str) -> bool:
    with get_session() as session:
        return session.get(ActivityRecord, activity_id) is not None


# ------------------------------------------------------------------
# Conversion helpers
# ------------------------------------------------------------------

def _record_to_activity(r: ActivityRecord) -> Activity:
    return Activity(
        id=r.id,
        name=r.name,
        duration=r.duration,
        predecessors=[p.strip() for p in r.predecessors.split(",") if p.strip()],
        ES=r.ES,
        EF=r.EF,
        LS=r.LS,
        LF=r.LF,
        total_float=r.total_float,
        is_critical=r.is_critical,
    )


def _activity_to_record(a: Activity) -> ActivityRecord:
    return ActivityRecord(
        id=a.id,
        name=a.name,
        duration=a.duration,
        predecessors=",".join(a.predecessors),
        ES=a.ES,
        EF=a.EF,
        LS=a.LS,
        LF=a.LF,
        total_float=a.total_float,
        is_critical=a.is_critical,
    )


def _update_record(record: ActivityRecord, a: Activity):
    record.name = a.name
    record.duration = a.duration
    record.predecessors = ",".join(a.predecessors)
    record.ES = a.ES
    record.EF = a.EF
    record.LS = a.LS
    record.LF = a.LF
    record.total_float = a.total_float
    record.is_critical = a.is_critical
