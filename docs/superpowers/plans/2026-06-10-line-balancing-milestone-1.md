# Line Balancing Milestone 1 (Scaffold + Models + Precedence + Metrics) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Project scaffold plus the shared foundation of the line balancing module: task data model, precedence-graph validation/helpers, and line-balance metrics — all tested, no UI yet.

**Architecture:** Pure-Python `core/line_balancing/` package (zero Streamlit imports) per the approved spec (`docs/superpowers/specs/2026-06-10-line-balancing-design.md`). Heuristics (milestones 2–4) and UI (milestone 5) are planned separately because heuristic tests depend on the owner's hand-solved exercises.

**Tech Stack:** Python 3.11+, pytest. (streamlit/plotly/networkx installed now, used in later milestones.)

**Teaching-mode note:** This is a learning project. Execute inline with the owner present. Task 4 contains a designated owner-written function (marked **OWNER WRITES**) — the tests fully define correct behavior, so this is not a placeholder.

**Course conventions (already confirmed — see spec):** ties broken by lower task ID; smoothness index vs. cycle time; cycle time from demand rounded down; efficiency `Σt/(n·CT)`; balance delay `1 − efficiency`; min stations `ceil(Σt/CT)`.

---

### Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`, `.gitignore`, `pyproject.toml`
- Create: `core/__init__.py`, `core/line_balancing/__init__.py`, `tests/__init__.py` (all empty)

- [ ] **Step 1: Create the virtual environment**

Run (PowerShell):
```powershell
python -m venv .venv
```

- [ ] **Step 2: Write `requirements.txt`**

```
streamlit>=1.35
plotly>=5.20
networkx>=3.2
pytest>=8.0
```

- [ ] **Step 3: Write `.gitignore`**

```
.venv/
__pycache__/
.pytest_cache/
*.pyc
```

- [ ] **Step 4: Write `pyproject.toml`** (makes `core` importable from tests without packaging ceremony)

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 5: Create the empty package files**

`core/__init__.py`, `core/line_balancing/__init__.py`, `tests/__init__.py` — all zero bytes.

- [ ] **Step 6: Install dependencies and verify pytest runs**

Run:
```powershell
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest
```
Expected: install succeeds; pytest reports "no tests ran" (exit code 5 is fine at this stage).

- [ ] **Step 7: Commit**

```powershell
git add requirements.txt .gitignore pyproject.toml core tests
git commit -m "chore: scaffold project structure and dependencies"
```

---

### Task 2: Task and Station data model

**Files:**
- Create: `core/line_balancing/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

`tests/test_models.py`:
```python
from core.line_balancing.models import Station, Task


def test_task_holds_id_duration_predecessors():
    t = Task(id="B", duration=4.0, predecessors=("A",))
    assert t.id == "B"
    assert t.duration == 4.0
    assert t.predecessors == ("A",)


def test_task_predecessors_default_to_empty():
    assert Task(id="A", duration=2.0).predecessors == ()


def test_station_total_and_idle_time():
    s = Station(index=1)
    s.tasks.extend([Task("A", 5.0), Task("B", 3.0)])
    assert s.total_time == 8.0
    assert s.idle_time(cycle_time=10.0) == 2.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv\Scripts\python -m pytest tests/test_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.line_balancing.models'`

- [ ] **Step 3: Write minimal implementation**

`core/line_balancing/models.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv\Scripts\python -m pytest tests/test_models.py -v`
Expected: 3 PASSED

- [ ] **Step 5: Commit**

```powershell
git add core/line_balancing/models.py tests/test_models.py
git commit -m "feat: add Task and Station data model"
```

---

### Task 3: Precedence validation and shared helpers

**Files:**
- Create: `core/line_balancing/precedence.py`
- Test: `tests/test_precedence.py`

- [ ] **Step 1: Write the failing tests**

`tests/test_precedence.py`:
```python
import pytest

from core.line_balancing.models import Station, Task
from core.line_balancing.precedence import (
    eligible_tasks,
    fits_in_station,
    validate_tasks,
)


def test_duplicate_task_ids_rejected():
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        validate_tasks([Task("A", 1.0), Task("A", 2.0)], cycle_time=10.0)


def test_unknown_predecessor_rejected():
    with pytest.raises(ValueError, match="unknown predecessor"):
        validate_tasks([Task("A", 1.0, ("Z",))], cycle_time=10.0)


def test_non_positive_duration_rejected():
    with pytest.raises(ValueError, match="positive"):
        validate_tasks([Task("A", 0.0)], cycle_time=10.0)


def test_duration_exceeding_cycle_time_rejected():
    with pytest.raises(ValueError, match="cycle time"):
        validate_tasks([Task("A", 12.0)], cycle_time=10.0)


def test_circular_precedence_rejected():
    tasks = [Task("A", 1.0, ("B",)), Task("B", 1.0, ("A",))]
    with pytest.raises(ValueError, match="[Cc]ircular"):
        validate_tasks(tasks, cycle_time=10.0)


def test_valid_input_passes():
    tasks = [Task("A", 2.0), Task("B", 3.0, ("A",))]
    validate_tasks(tasks, cycle_time=10.0)  # must not raise


def test_eligible_tasks_respects_predecessors():
    tasks = [Task("A", 2.0), Task("B", 3.0, ("A",)), Task("C", 1.0, ("A", "B"))]
    assert [t.id for t in eligible_tasks(tasks, assigned_ids=set())] == ["A"]
    assert [t.id for t in eligible_tasks(tasks, assigned_ids={"A"})] == ["B"]
    assert [t.id for t in eligible_tasks(tasks, assigned_ids={"A", "B"})] == ["C"]


def test_fits_in_station():
    s = Station(index=1, tasks=[Task("A", 7.0)])
    assert fits_in_station(Task("B", 3.0), s, cycle_time=10.0)
    assert not fits_in_station(Task("C", 4.0), s, cycle_time=10.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests/test_precedence.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.line_balancing.precedence'`

- [ ] **Step 3: Write the implementation**

`core/line_balancing/precedence.py`:
```python
"""Input validation and precedence helpers shared by all heuristics."""
from .models import Station, Task


def validate_tasks(tasks: list[Task], cycle_time: float) -> None:
    """Raise ValueError describing the first problem found in the input."""
    ids = [t.id for t in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate task IDs in input.")
    id_set = set(ids)
    for t in tasks:
        if t.duration <= 0:
            raise ValueError(f"Task {t.id}: duration must be positive.")
        if t.duration > cycle_time:
            raise ValueError(
                f"Task {t.id}: duration {t.duration} exceeds cycle time "
                f"{cycle_time}; it can never fit in a station."
            )
        for p in t.predecessors:
            if p not in id_set:
                raise ValueError(f"Task {t.id} references unknown predecessor {p}.")
    _check_acyclic(tasks)


def _check_acyclic(tasks: list[Task]) -> None:
    # Kahn-style elimination: keep removing tasks whose predecessors are all
    # removed. If we get stuck with tasks remaining, those form a cycle.
    remaining = {t.id: set(t.predecessors) for t in tasks}
    while remaining:
        free = [tid for tid, preds in remaining.items() if not preds]
        if not free:
            raise ValueError(
                f"Circular precedence among tasks: {sorted(remaining)}"
            )
        for tid in free:
            del remaining[tid]
        for preds in remaining.values():
            preds.difference_update(free)


def eligible_tasks(tasks: list[Task], assigned_ids: set[str]) -> list[Task]:
    """Unassigned tasks whose predecessors have all been assigned."""
    return [
        t
        for t in tasks
        if t.id not in assigned_ids
        and all(p in assigned_ids for p in t.predecessors)
    ]


def fits_in_station(task: Task, station: Station, cycle_time: float) -> bool:
    return station.total_time + task.duration <= cycle_time
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\python -m pytest tests/test_precedence.py -v`
Expected: 8 PASSED

- [ ] **Step 5: Commit**

```powershell
git add core/line_balancing/precedence.py tests/test_precedence.py
git commit -m "feat: add precedence validation and shared eligibility helpers"
```

---

### Task 4: Line-balance metrics

**Files:**
- Create: `core/line_balancing/metrics.py`
- Test: `tests/test_metrics.py`

- [ ] **Step 1: Write the failing tests** (these encode the confirmed course conventions)

`tests/test_metrics.py`:
```python
import math

import pytest

from core.line_balancing.metrics import (
    balance_delay,
    cycle_time_from_demand,
    line_efficiency,
    smoothness_index,
    theoretical_min_stations,
)
from core.line_balancing.models import Station, Task


def make_stations(*times: float) -> list[Station]:
    return [
        Station(index=i + 1, tasks=[Task(f"T{i}", time)])
        for i, time in enumerate(times)
    ]


def test_cycle_time_from_demand_rounds_down():
    # 480 min available / 70 units = 6.857... -> 6 (course convention: floor,
    # so the line is fast enough to meet demand)
    assert cycle_time_from_demand(available_time=480, demand=70) == 6


def test_cycle_time_exact_division_unchanged():
    assert cycle_time_from_demand(available_time=480, demand=60) == 8


def test_theoretical_min_stations_rounds_up():
    tasks = [Task("A", 5.0), Task("B", 4.0), Task("C", 3.0)]  # sum = 12
    assert theoretical_min_stations(tasks, cycle_time=5.0) == 3  # 12/5 = 2.4 -> 3


def test_line_efficiency():
    stations = make_stations(8.0, 4.0)  # total work 12, capacity 2 * 8 = 16
    assert line_efficiency(stations, cycle_time=8.0) == pytest.approx(0.75)


def test_balance_delay_is_complement_of_efficiency():
    stations = make_stations(8.0, 4.0)
    assert balance_delay(stations, cycle_time=8.0) == pytest.approx(0.25)


def test_smoothness_index_measured_against_cycle_time():
    # Course convention: SI = sqrt(sum((CT - station_time)^2))
    stations = make_stations(8.0, 6.0)
    expected = math.sqrt((10.0 - 8.0) ** 2 + (10.0 - 6.0) ** 2)
    assert smoothness_index(stations, cycle_time=10.0) == pytest.approx(expected)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\python -m pytest tests/test_metrics.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'core.line_balancing.metrics'`

- [ ] **Step 3: Write the module skeleton; OWNER WRITES the formula bodies**

These formulas are exactly what the owner learned in class — they write
`line_efficiency`, `balance_delay`, and `smoothness_index` (the tests define
correct behavior). The executor writes the file with those three bodies as
`raise NotImplementedError` and asks the owner to fill them in (5–10 lines
total) before continuing.

`core/line_balancing/metrics.py` (as handed to the owner):
```python
"""Line-balance performance metrics.

Conventions follow the owner's course (see design spec):
- cycle time from demand is rounded DOWN so demand is always met
- smoothness index is measured against the cycle time, not the max station
"""
import math

from .models import Station, Task


def cycle_time_from_demand(available_time: float, demand: int) -> int:
    return math.floor(available_time / demand)


def theoretical_min_stations(tasks: list[Task], cycle_time: float) -> int:
    return math.ceil(sum(t.duration for t in tasks) / cycle_time)


def line_efficiency(stations: list[Station], cycle_time: float) -> float:
    # OWNER WRITES: efficiency = (sum of all task times) / (n_stations * CT)
    raise NotImplementedError


def balance_delay(stations: list[Station], cycle_time: float) -> float:
    # OWNER WRITES: the share of paid station time that is idle
    raise NotImplementedError


def smoothness_index(stations: list[Station], cycle_time: float) -> float:
    # OWNER WRITES: sqrt of the sum of squared (CT - station_time) gaps
    raise NotImplementedError
```

- [ ] **Step 4: Owner fills in the three bodies; run tests until they pass**

Run: `.venv\Scripts\python -m pytest tests/test_metrics.py -v`
Expected: 6 PASSED. If a test fails, walk through the formula together — do
not silently rewrite the owner's code (CLAUDE.md quality rule).

- [ ] **Step 5: Run the full suite**

Run: `.venv\Scripts\python -m pytest -v`
Expected: all tests pass (models + precedence + metrics).

- [ ] **Step 6: Commit**

```powershell
git add core/line_balancing/metrics.py tests/test_metrics.py
git commit -m "feat: add line-balance metrics with course conventions"
```

---

### Task 5: Milestone checkpoint

- [ ] **Step 1: Walk the owner through every file written in this milestone**, file by file, per CLAUDE.md teaching mode. Do not proceed to milestone 2 (Largest Candidate Rule) until the owner confirms understanding and provides their first hand-solved LCR exercise.
