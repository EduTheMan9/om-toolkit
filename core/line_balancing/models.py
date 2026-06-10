"""Data model for assembly line balancing.

Tasks are immutable inputs; Stations are built up by the heuristics.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Task:
    id: str
    duration: float
    predecessors: tuple[str, ...] = ()


@dataclass
class Station:
    index: int
    tasks: list[Task] = field(default_factory=list)

    @property
    def total_time(self) -> float:
        return sum(t.duration for t in self.tasks)

    def idle_time(self, cycle_time: float) -> float:
        return cycle_time - self.total_time
