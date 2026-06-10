"""Data model for process analysis.

A process is an ordered list of Resources. Units are caller's choice:
capacity comes out in units per the same time unit as processing_time.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Resource:
    name: str
    processing_time: float  # time to process one unit (per server)
    servers: int = 1

    @property
    def capacity(self) -> float:
        return self.servers / self.processing_time
