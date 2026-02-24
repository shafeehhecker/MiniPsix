"""
Activity data model for Mini-P6 CPM Scheduler.

This module defines the `Activity` dataclass, which represents a single project
activity (task) in a Critical Path Method (CPM) network. Each activity stores
scheduling attributes and the CPM-computed forward/backward pass results used to
identify the critical path, floats, and schedule dates.

CPM Terminology recap
----------------------
ES  – Early Start  : earliest time the activity *can* begin
EF  – Early Finish : ES + duration  (computed in forward pass)
LS  – Late Start   : LF - duration  (computed in backward pass)
LF  – Late Finish  : latest time the activity *must* finish without delaying the project
TF  – Total Float  : LS - ES  (or LF - EF); slack available without delaying project end
FF  – Free Float   : how much an activity can slip without delaying any *successor's* ES
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _parse_predecessors(value: Any) -> List[str]:
    """
    Normalise a predecessor specification into a list of activity-ID strings.

    Accepts:
        - A list already in the correct form: ``["A", "B"]``
        - A comma-separated string:          ``"A, B"``
        - An empty string / None:            ``""`` / ``None``
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(p).strip() for p in value if str(p).strip()]
    if isinstance(value, str):
        return [p.strip() for p in value.split(",") if p.strip()]
    raise TypeError(f"predecessors must be a list or comma-separated string, got {type(value)}")


# ---------------------------------------------------------------------------
# Main dataclass
# ---------------------------------------------------------------------------

@dataclass
class Activity:
    """
    Represents a single CPM project activity.

    Parameters
    ----------
    id : str
        Unique identifier for the activity (e.g. ``"A"``, ``"T10"``).
    name : str
        Human-readable activity name / description.
    duration : int
        Activity duration in the project's time unit (days, weeks, …).
        Must be a non-negative integer.
    predecessors : list[str] | str, optional
        IDs of activities that must finish before this one can start
        (Finish-to-Start relationships only).  Accepts a Python list *or*
        a comma-separated string for easy CSV import.
    resource : str, optional
        Responsible resource / team name (informational, not used in CPM math).
    description : str, optional
        Extended notes or scope description for the activity.

    CPM Computed Fields (set by the scheduler, not the user)
    --------------------------------------------------------
    ES, EF, LS, LF : int
        Forward- and backward-pass schedule dates.
    total_float : int
        Total float (= LS - ES).
    free_float : int
        Free float – how much the activity can slip without delaying any
        immediate successor's Early Start.
    is_critical : bool
        ``True`` when total_float == 0 (activity lies on the critical path).
    """

    # --- Required user-supplied fields ---
    id: str
    name: str
    duration: int

    # --- Optional user-supplied fields ---
    predecessors: List[str] = field(default_factory=list)
    resource: Optional[str] = None
    description: Optional[str] = None

    # --- CPM computed fields (populated by the scheduler) ---
    ES: int = 0
    EF: int = 0
    LS: int = 0
    LF: int = 0
    total_float: int = 0
    free_float: int = 0
    is_critical: bool = False

    # ------------------------------------------------------------------ #
    # Initialisation & validation                                          #
    # ------------------------------------------------------------------ #

    def __post_init__(self) -> None:
        """Validate inputs and normalise predecessors after construction."""

        # Normalise id
        self.id = str(self.id).strip()
        if not self.id:
            raise ValueError("Activity 'id' must be a non-empty string.")

        # Normalise name
        self.name = str(self.name).strip()
        if not self.name:
            raise ValueError("Activity 'name' must be a non-empty string.")

        # Validate duration
        if not isinstance(self.duration, int) or self.duration < 0:
            raise ValueError(
                f"Activity duration must be a non-negative integer, got {self.duration!r}."
            )

        # Normalise predecessors (accept list *or* comma-separated string)
        self.predecessors = _parse_predecessors(self.predecessors)

        # Guard: an activity cannot be its own predecessor
        if self.id in self.predecessors:
            raise ValueError(
                f"Activity '{self.id}' lists itself as a predecessor, which would create a self-loop."
            )

    # ------------------------------------------------------------------ #
    # Computed properties                                                  #
    # ------------------------------------------------------------------ #

    @property
    def schedule_dates(self) -> Dict[str, int]:
        """Return all four schedule dates as a compact mapping."""
        return {"ES": self.ES, "EF": self.EF, "LS": self.LS, "LF": self.LF}

    @property
    def has_float(self) -> bool:
        """``True`` if the activity has any total float (i.e. is *not* critical)."""
        return self.total_float > 0

    # ------------------------------------------------------------------ #
    # CPM helpers (called by the scheduler)                                #
    # ------------------------------------------------------------------ #

    def compute_early_finish(self) -> None:
        """Set EF = ES + duration.  Call after ES has been assigned."""
        self.EF = self.ES + self.duration

    def compute_late_start(self) -> None:
        """Set LS = LF - duration.  Call after LF has been assigned."""
        self.LS = self.LF - self.duration

    def compute_floats(self) -> None:
        """
        Compute Total Float and update the ``is_critical`` flag.

        Total Float = LS - ES  (equivalently LF - EF).
        Free Float must be set externally by the scheduler once all
        successors' ES values are known.
        """
        self.total_float = self.LS - self.ES
        self.is_critical = self.total_float == 0

    def reset_cpm_fields(self) -> None:
        """
        Reset all CPM computed fields to their default values.

        Useful when re-running the scheduler on a modified network without
        creating new Activity objects.
        """
        self.ES = 0
        self.EF = 0
        self.LS = 0
        self.LF = 0
        self.total_float = 0
        self.free_float = 0
        self.is_critical = False

    # ------------------------------------------------------------------ #
    # Serialisation                                                        #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialise the activity to a plain dictionary.

        The ``predecessors`` list is stored as a comma-separated string so
        the dict can be written directly to CSV / Excel rows.
        """
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "predecessors": ",".join(self.predecessors),
            "resource": self.resource or "",
            "description": self.description or "",
            "ES": self.ES,
            "EF": self.EF,
            "LS": self.LS,
            "LF": self.LF,
            "total_float": self.total_float,
            "free_float": self.free_float,
            "is_critical": self.is_critical,
        }

    def to_json(self, **kwargs) -> str:
        """Return the activity serialised as a JSON string."""
        return json.dumps(self.to_dict(), **kwargs)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Activity":
        """
        Deserialise an Activity from a dictionary (e.g. a CSV row).

        All CPM fields are optional in the source dict; they default to 0 /
        ``False`` when absent so that freshly imported activities can be
        scheduled from scratch.
        """
        preds = _parse_predecessors(data.get("predecessors", ""))

        return cls(
            id=str(data["id"]).strip(),
            name=str(data["name"]).strip(),
            duration=int(data["duration"]),
            predecessors=preds,
            resource=data.get("resource") or None,
            description=data.get("description") or None,
            ES=int(data.get("ES", 0)),
            EF=int(data.get("EF", 0)),
            LS=int(data.get("LS", 0)),
            LF=int(data.get("LF", 0)),
            total_float=int(data.get("total_float", 0)),
            free_float=int(data.get("free_float", 0)),
            is_critical=bool(data.get("is_critical", False)),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "Activity":
        """Deserialise an Activity from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    # ------------------------------------------------------------------ #
    # Display helpers                                                      #
    # ------------------------------------------------------------------ #

    def summary(self) -> str:
        """
        Return a single-line human-readable summary of the activity.

        Example output::

            [CRITICAL] A | Foundation Work | dur=5 | ES=0 EF=5 LS=0 LF=5 | TF=0 FF=0
        """
        tag = "[CRITICAL]" if self.is_critical else "[float={:>3}]".format(self.total_float)
        preds_str = ",".join(self.predecessors) if self.predecessors else "—"
        return (
            f"{tag} {self.id} | {self.name} | dur={self.duration} | "
            f"pred=[{preds_str}] | "
            f"ES={self.ES} EF={self.EF} LS={self.LS} LF={self.LF} | "
            f"TF={self.total_float} FF={self.free_float}"
        )

    def __repr__(self) -> str:
        return (
            f"Activity(id={self.id!r}, name={self.name!r}, duration={self.duration}, "
            f"predecessors={self.predecessors!r}, critical={self.is_critical})"
        )

    def __eq__(self, other: object) -> bool:
        """Two activities are considered equal if they share the same ``id``."""
        if not isinstance(other, Activity):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
