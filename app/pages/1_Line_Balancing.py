import pandas as pd
import streamlit as st

from app.charts import precedence_figure, stations_figure
from app.examples import EXAMPLES
from core.line_balancing import (
    Task,
    balance_delay,
    cycle_time_from_demand,
    kilbridge_wester,
    largest_candidate_rule,
    line_efficiency,
    ranked_positional_weight,
    smoothness_index,
    theoretical_min_stations,
    validate_tasks,
)

HEURISTICS = {
    "Largest Candidate Rule": largest_candidate_rule,
    "Ranked Positional Weight": ranked_positional_weight,
    "Kilbridge–Wester": kilbridge_wester,
}

st.set_page_config(page_title="Line Balancing — OM Toolkit", page_icon="⚖️", layout="wide")
st.title("⚖️ Assembly Line Balancing")


def parse_tasks(rows: list[dict]) -> list[Task]:
    tasks = []
    for row in rows:
        task_id = str(row.get("Task") or "").strip()
        if not task_id:
            continue  # ignore blank editor rows
        raw_preds = str(row.get("Predecessors") or "")
        predecessors = tuple(
            p.strip() for p in raw_preds.replace(";", ",").split(",")
            if p.strip() and p.strip() not in ("-", "—")
        )
        duration = row.get("Duration")
        # an empty editor cell arrives as NaN, which float() would accept silently
        duration = 0.0 if duration is None or pd.isna(duration) else float(duration)
        tasks.append(Task(task_id, duration, predecessors))
    return tasks


# --- Input ------------------------------------------------------------------
example_name = st.selectbox("Load an example", list(EXAMPLES))
example = EXAMPLES[example_name]
st.caption(example["description"])

left, right = st.columns([3, 2])

with left:
    st.subheader("Tasks")
    # Keying the editor by example name gives a fresh table when the user
    # switches examples, while preserving their edits otherwise.
    edited = st.data_editor(
        pd.DataFrame(example["rows"]),
        num_rows="dynamic",
        width="stretch",
        key=f"editor_{example_name}",
        column_config={
            "Task": st.column_config.TextColumn(required=True),
            "Duration": st.column_config.NumberColumn(min_value=0.0),
            "Predecessors": st.column_config.TextColumn(
                help="Comma-separated task IDs, e.g. 'A, B'. Leave empty for none."
            ),
        },
    )

with right:
    st.subheader("Cycle time")
    mode = st.radio(
        "How is the cycle time defined?",
        ["Enter directly", "From demand"],
        horizontal=True,
        key=f"ct_mode_{example_name}",
    )
    if mode == "Enter directly":
        cycle_time = st.number_input(
            "Cycle time", min_value=0.1, value=float(example["cycle_time"]),
            key=f"ct_{example_name}",
        )
    else:
        available = st.number_input("Available production time", min_value=1.0, value=480.0)
        demand = st.number_input("Demand (units)", min_value=1, value=60)
        cycle_time = float(cycle_time_from_demand(available, int(demand)))
        st.metric("Cycle time = ⌊available / demand⌋", f"{cycle_time:g}")

tasks = parse_tasks(edited.to_dict("records"))
if not tasks:
    st.info("Add at least one task.")
    st.stop()
try:
    validate_tasks(tasks, cycle_time)
except ValueError as err:
    st.error(str(err))
    st.stop()

# --- Problem overview ---------------------------------------------------------
st.subheader("Precedence diagram")
st.plotly_chart(precedence_figure(tasks), width="stretch")

total_work = sum(t.duration for t in tasks)
n_min = theoretical_min_stations(tasks, cycle_time)
c1, c2, c3 = st.columns(3)
c1.metric("Total work content", f"{total_work:g}")
c2.metric("Cycle time", f"{cycle_time:g}")
c3.metric("Theoretical min. stations", n_min)

# --- Solve and compare --------------------------------------------------------
st.subheader("Heuristic comparison")
results = {name: solve(tasks, cycle_time) for name, solve in HEURISTICS.items()}

comparison = pd.DataFrame(
    {
        "Stations": [len(s) for s in results.values()],
        "Efficiency": [f"{line_efficiency(s, cycle_time):.1%}" for s in results.values()],
        "Balance delay": [f"{balance_delay(s, cycle_time):.1%}" for s in results.values()],
        "Smoothness index": [f"{smoothness_index(s, cycle_time):.2f}" for s in results.values()],
    },
    index=list(results),
)
st.dataframe(comparison, width="stretch")

for name, tab in zip(results, st.tabs(list(results))):
    stations = results[name]
    with tab:
        # explicit keys: two heuristics can produce identical figures/tables,
        # which would collide in Streamlit's auto-generated element IDs
        st.plotly_chart(
            stations_figure(stations, cycle_time),
            width="stretch",
            key=f"stations_{name}",
        )
        idle = pd.DataFrame(
            {
                "Station": [s.index for s in stations],
                "Tasks": [", ".join(t.id for t in s.tasks) for s in stations],
                "Station time": [s.total_time for s in stations],
                "Idle time": [s.idle_time(cycle_time) for s in stations],
            }
        )
        st.dataframe(idle, hide_index=True, width="stretch", key=f"idle_{name}")
