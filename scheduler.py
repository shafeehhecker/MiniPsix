"""
CPM Scheduling Engine for Mini-P6.
Performs Forward Pass, Backward Pass, Float calculation, and Critical Path identification.
"""
from typing import Dict, List, Optional, Tuple
from collections import deque
from .activity import Activity


class SchedulerError(Exception):
    pass


class CPMScheduler:
    """
    Critical Path Method engine.

    Algorithm:
    1. Build a directed graph from activity dependencies
    2. Topological sort (Kahn's algorithm)
    3. Forward pass  → compute ES / EF
    4. Backward pass → compute LS / LF
    5. Float = LS - ES  (or LF - EF)
    6. Critical path  = all activities where Float == 0
    """

    def __init__(self, activities: Dict[str, Activity]):
        self.activities = activities  # {id: Activity}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def schedule(self) -> List[Activity]:
        """Run full CPM and return activities with all fields populated."""
        if not self.activities:
            return []

        self._validate()
        order = self._topological_sort()
        self._forward_pass(order)
        self._backward_pass(order)
        self._compute_float()

        return list(self.activities.values())

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self):
        for act_id, act in self.activities.items():
            for pred_id in act.predecessors:
                if pred_id not in self.activities:
                    raise SchedulerError(
                        f"Activity '{act_id}' references unknown predecessor '{pred_id}'"
                    )

    # ------------------------------------------------------------------
    # Topological sort (Kahn's BFS)
    # ------------------------------------------------------------------

    def _topological_sort(self) -> List[str]:
        in_degree: Dict[str, int] = {aid: 0 for aid in self.activities}
        successors: Dict[str, List[str]] = {aid: [] for aid in self.activities}

        for act_id, act in self.activities.items():
            for pred_id in act.predecessors:
                successors[pred_id].append(act_id)
                in_degree[act_id] += 1

        # Start with activities that have no predecessors
        queue = deque(aid for aid, deg in in_degree.items() if deg == 0)
        order: List[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)
            for succ in successors[current]:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        if len(order) != len(self.activities):
            raise SchedulerError(
                "Circular dependency detected in activity network. "
                "Please check predecessor relationships."
            )

        return order

    # ------------------------------------------------------------------
    # Forward pass: compute ES and EF
    # ------------------------------------------------------------------

    def _forward_pass(self, order: List[str]):
        for act_id in order:
            act = self.activities[act_id]
            if not act.predecessors:
                act.ES = 0
            else:
                act.ES = max(
                    self.activities[pred_id].EF for pred_id in act.predecessors
                )
            act.EF = act.ES + act.duration

    # ------------------------------------------------------------------
    # Backward pass: compute LS and LF
    # ------------------------------------------------------------------

    def _backward_pass(self, order: List[str]):
        # Project finish = maximum EF across all activities
        project_finish = max(act.EF for act in self.activities.values())

        # Build successor map
        successors: Dict[str, List[str]] = {aid: [] for aid in self.activities}
        for act_id, act in self.activities.items():
            for pred_id in act.predecessors:
                successors[pred_id].append(act_id)

        # Process in reverse topological order
        for act_id in reversed(order):
            act = self.activities[act_id]
            if not successors[act_id]:
                act.LF = project_finish
            else:
                act.LF = min(
                    self.activities[succ_id].LS for succ_id in successors[act_id]
                )
            act.LS = act.LF - act.duration

    # ------------------------------------------------------------------
    # Float and critical path
    # ------------------------------------------------------------------

    def _compute_float(self):
        for act in self.activities.values():
            act.total_float = act.LS - act.ES
            act.is_critical = act.total_float == 0

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def get_critical_path(self) -> List[str]:
        """Return IDs of critical activities in order."""
        return [
            act_id
            for act_id, act in self.activities.items()
            if act.is_critical
        ]

    def project_duration(self) -> int:
        if not self.activities:
            return 0
        return max(act.EF for act in self.activities.values())
