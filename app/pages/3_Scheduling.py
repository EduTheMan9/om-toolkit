import pandas as pd
import streamlit as st

from app.examples import DISPATCH_EXAMPLES, JOHNSON_EXAMPLES
from app.scheduling_charts import rules_gantt, two_machine_gantt
from core.scheduling import (
    RULES,
    FlowShopJob,
    Job,
    build_schedule,
    flow_shop_schedule,
    johnson_sequence,
    schedule_metrics,
    validate_flow_shop_jobs,
    validate_jobs,
)

st.set_page_config(page_title="Scheduling — OM Toolkit", page_icon="📅", layout="wide")
st.title("📅 Scheduling")


def _num(row: dict, column: str) -> float:
    value = row.get(column)
    return 0.0 if value is None or pd.isna(value) else float(value)


dispatch_tab, johnson_tab = st.tabs(
    ["Single machine — dispatching rules", "Two machines — Johnson's rule"]
)

# --- Tab 1: dispatching rules -------------------------------------------------
with dispatch_tab:
    example_name = st.selectbox("Load an example", list(DISPATCH_EXAMPLES))
    example = DISPATCH_EXAMPLES[example_name]
    st.caption(example["description"] + " All times in the same unit (e.g. hours).")

    edited = st.data_editor(
        pd.DataFrame(example["rows"]),
        num_rows="dynamic",
        width="stretch",
        key=f"dispatch_{example_name}",
        column_config={
            "Job": st.column_config.TextColumn(required=True),
            "Processing time": st.column_config.NumberColumn(min_value=0.0),
            "Due date": st.column_config.NumberColumn(min_value=0.0),
        },
    )

    jobs = [
        Job(str(r["Job"]).strip(), _num(r, "Processing time"), _num(r, "Due date"))
        for r in edited.to_dict("records")
        if str(r.get("Job") or "").strip()
    ]
    try:
        validate_jobs(jobs)
    except ValueError as err:
        st.error(str(err))
        st.stop()

    schedules = {rule: build_schedule(order(jobs)) for rule, order in RULES.items()}

    comparison = pd.DataFrame(
        {
            "Sequence": [" → ".join(s.id for s in sched) for sched in schedules.values()],
            "Avg completion": [
                f"{schedule_metrics(sched, jobs)['avg_completion_time']:.2f}"
                for sched in schedules.values()
            ],
            "Avg tardiness": [
                f"{schedule_metrics(sched, jobs)['avg_tardiness']:.2f}"
                for sched in schedules.values()
            ],
            "Max tardiness": [
                f"{schedule_metrics(sched, jobs)['max_tardiness']:g}"
                for sched in schedules.values()
            ],
            "Tardy jobs": [
                schedule_metrics(sched, jobs)["num_tardy"] for sched in schedules.values()
            ],
        },
        index=list(schedules),
    )
    st.dataframe(comparison, width="stretch", key="rule_comparison")
    st.caption(
        "Classic results to look for: SPT minimizes average completion/flow "
        "time; EDD minimizes maximum lateness."
    )

    due_dates = {j.id: j.due_date for j in jobs}
    st.plotly_chart(rules_gantt(schedules, due_dates), width="stretch", key="rules_gantt")

# --- Tab 2: Johnson's rule ------------------------------------------------------
with johnson_tab:
    example_name = st.selectbox("Load an example", list(JOHNSON_EXAMPLES), key="j_example")
    example = JOHNSON_EXAMPLES[example_name]
    st.caption(example["description"] + " Every job visits machine 1, then machine 2.")

    edited = st.data_editor(
        pd.DataFrame(example["rows"]),
        num_rows="dynamic",
        width="stretch",
        key=f"johnson_{example_name}",
        column_config={
            "Job": st.column_config.TextColumn(required=True),
            "Machine 1 time": st.column_config.NumberColumn(min_value=0.0),
            "Machine 2 time": st.column_config.NumberColumn(min_value=0.0),
        },
    )

    fs_jobs = [
        FlowShopJob(
            str(r["Job"]).strip(), _num(r, "Machine 1 time"), _num(r, "Machine 2 time")
        )
        for r in edited.to_dict("records")
        if str(r.get("Job") or "").strip()
    ]
    try:
        validate_flow_shop_jobs(fs_jobs)
    except ValueError as err:
        st.error(str(err))
        st.stop()

    sequence = johnson_sequence(fs_jobs)
    schedule = flow_shop_schedule(sequence)

    c1, c2 = st.columns([3, 1])
    c1.metric("Johnson sequence", " → ".join(j.id for j in sequence))
    c2.metric("Makespan", f"{schedule.makespan:g}")

    st.plotly_chart(two_machine_gantt(schedule), width="stretch", key="johnson_gantt")
    m2_busy = sum(s.end - s.start for s in schedule.machine2)
    st.caption(
        f"Machine 2 is idle {schedule.makespan - m2_busy:g} of {schedule.makespan:g} "
        "time units — Johnson's rule front-loads short machine-1 jobs precisely "
        "to keep that idle time small."
    )
