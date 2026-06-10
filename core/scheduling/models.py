"""Data model for scheduling problems."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Job:
    """A job for single-machine dispatching (all jobs available at t = 0)."""
    id: str
    processing_time: float
    due_date: float | None = None


@dataclass(frozen=True)
class FlowShopJob:
    """A job for the two-machine flow shop (machine 1 then machine 2)."""
    id: str
    time_m1: float
    time_m2: float


@dataclass(frozen=True)
class ScheduledJob:
    """A job placed on a timeline."""
    id: str
    start: float
    end: float
