"""
Activity data model for Mini-P6 CPM Scheduler.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Activity:
    id: str
    name: str
    duration: int
    predecessors: List[str] = field(default_factory=list)

    # CPM calculated fields
    ES: int = 0   # Early Start
    EF: int = 0   # Early Finish
    LS: int = 0   # Late Start
    LF: int = 0   # Late Finish
    total_float: int = 0
    is_critical: bool = False

    def __post_init__(self):
        if isinstance(self.predecessors, str):
            # Handle comma-separated string input
            self.predecessors = [p.strip() for p in self.predecessors.split(",") if p.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "duration": self.duration,
            "predecessors": ",".join(self.predecessors),
            "ES": self.ES,
            "EF": self.EF,
            "LS": self.LS,
            "LF": self.LF,
            "total_float": self.total_float,
            "is_critical": self.is_critical,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Activity":
        preds = data.get("predecessors", "")
        if isinstance(preds, str):
            preds = [p.strip() for p in preds.split(",") if p.strip()]
        return cls(
            id=data["id"],
            name=data["name"],
            duration=int(data["duration"]),
            predecessors=preds,
            ES=int(data.get("ES", 0)),
            EF=int(data.get("EF", 0)),
            LS=int(data.get("LS", 0)),
            LF=int(data.get("LF", 0)),
            total_float=int(data.get("total_float", 0)),
            is_critical=bool(data.get("is_critical", False)),
        )
