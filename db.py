"""
Database access layer for Mini-P7.
Provides simple CRUD operations for Activity records.

Fixes applied
-------------
* Raw SQL string replaced with SQLAlchemy ``text()`` (required in SA 2.x).
* Table name corrected from ``activity_record`` → ``activities`` (matches models.py).
* ``resource``, ``description``, and ``free_float`` fields added everywhere.
* ``load_all_activities`` rewritten to use the ORM directly (no raw SQL).
* ``_record_to_activity`` / ``_activity_to_record`` updated for all fields.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Dict, Optional
#typing import unused 
from models import Base, ActivityRecord
from activity import Activity


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
    """
    Load all activities from DB and return as {id: Activity} dict.

    FIX: previously used raw SQL with wrong table name ('activity_record')
         and missing resource/description/free_float columns.
         Now uses ORM query directly.
    """
    with get_session() as session:
        records = session.query(ActivityRecord).all()
        return {r.id: _record_to_activity(r) for r in records}


def save_activity(activity: Activity):
    """
    Insert or update a single activity.

    Uses session.merge to combine the check and write in one operation.
    """
    with get_session() as session:
        record = _activity_to_record(activity)
        session.merge(record)
        session.commit()


def save_all_activities(activities: Dict[str, Activity]):
    """
    Bulk save / update all activities (used after CPM run).

    FIX: added resource, description, free_float to insert/update mappings.
    """
    with get_session() as session:
        existing_ids = {row[0] for row in session.query(ActivityRecord.id).all()}

        insert_mappings = []
        update_mappings = []
        for act in activities.values():
            mapping = {
                "id":           act.id,
                "name":         act.name,
                "duration":     act.duration,
                "predecessors": ",".join(act.predecessors),
                "resource":     act.resource or "",
                "description":  act.description or "",
                "ES":           act.ES,
                "EF":           act.EF,
                "LS":           act.LS,
                "LF":           act.LF,
                "total_float":  act.total_float,
                "free_float":   act.free_float,
                "is_critical":  act.is_critical,
            }
            if act.id in existing_ids:
                update_mappings.append(mapping)
            else:
                insert_mappings.append(mapping)

        if insert_mappings:
            session.bulk_insert_mappings(ActivityRecord, insert_mappings)
        if update_mappings:
            session.bulk_update_mappings(ActivityRecord, update_mappings)

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
        return (
            session.query(ActivityRecord)
            .filter(ActivityRecord.id == activity_id)
            .first()
        ) is not None


# ------------------------------------------------------------------
# Conversion helpers
# ------------------------------------------------------------------

def _record_to_activity(r: ActivityRecord) -> Activity:
    """FIX: now includes resource, description, free_float."""
    preds = tuple(p.strip() for p in r.predecessors.split(",") if p.strip())
    return Activity(
        id=r.id,
        name=r.name,
        duration=r.duration,
        predecessors=preds,
        resource=r.resource or None,
        description=r.description or None,
        ES=r.ES,
        EF=r.EF,
        LS=r.LS,
        LF=r.LF,
        total_float=r.total_float,
        free_float=r.free_float,
        is_critical=r.is_critical,
    )


def _activity_to_record(a: Activity) -> ActivityRecord:
    """FIX: now includes resource, description, free_float."""
    return ActivityRecord(
        id=a.id,
        name=a.name,
        duration=a.duration,
        predecessors=",".join(a.predecessors),
        resource=a.resource or "",
        description=a.description or "",
        ES=a.ES,
        EF=a.EF,
        LS=a.LS,
        LF=a.LF,
        total_float=a.total_float,
        free_float=a.free_float,
        is_critical=a.is_critical,
    )

