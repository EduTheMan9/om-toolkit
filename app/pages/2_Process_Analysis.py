import pandas as pd
import streamlit as st

from app.examples import PROCESS_EXAMPLES
from app.process_charts import capacity_figure, utilization_figure
from core.process_analysis import (
    Resource,
    bottleneck,
    flow_rate,
    implied_utilization,
    process_capacity,
    solve_littles_law,
    unloaded_flow_time,
    utilization,
    validate_resources,
)

st.set_page_config(page_title="Process Analysis — OM Toolkit", page_icon="🔍", layout="wide")
st.title("🔍 Process Analysis & Bottleneck")


def parse_resources(rows: list[dict]) -> list[Resource]:
    resources = []
    for row in rows:
        name = str(row.get("Resource") or "").strip()
        if not name:
            continue  # ignore blank editor rows
        time_min = row.get("Processing time (min)")
        time_min = 0.0 if time_min is None or pd.isna(time_min) else float(time_min)
        servers = row.get("Servers")
        servers = 0 if servers is None or pd.isna(servers) else int(servers)
        resources.append(Resource(name, processing_time=time_min, servers=servers))
    return resources


# --- Input ------------------------------------------------------------------
example_name = st.selectbox("Load an example", list(PROCESS_EXAMPLES))
example = PROCESS_EXAMPLES[example_name]
st.caption(example["description"])

left, right = st.columns([3, 2])

with left:
    st.subheader("Process steps (in order)")
    edited = st.data_editor(
        pd.DataFrame(example["rows"]),
        num_rows="dynamic",
        width="stretch",
        key=f"editor_{example_name}",
        column_config={
            "Resource": st.column_config.TextColumn(required=True),
            "Processing time (min)": st.column_config.NumberColumn(min_value=0.0),
            "Servers": st.column_config.NumberColumn(min_value=1, step=1),
        },
    )

with right:
    st.subheader("Demand")
    demand_known = st.checkbox("Demand is known", value=True, key=f"dk_{example_name}")
    demand_per_hour = None
    if demand_known:
        demand_per_hour = st.number_input(
            "Demand (units/hour)", min_value=0.1,
            value=float(example["demand_per_hour"]),
            key=f"demand_{example_name}",
        )

resources = parse_resources(edited.to_dict("records"))
try:
    validate_resources(resources)
except ValueError as err:
    st.error(str(err))
    st.stop()

# Core works in minutes; the UI displays per-hour figures.
demand_per_min = None if demand_per_hour is None else demand_per_hour / 60
rate_per_min = flow_rate(resources, demand_per_min)

# --- Results ------------------------------------------------------------------
bn = bottleneck(resources)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bottleneck", bn.name)
c2.metric("Process capacity", f"{process_capacity(resources) * 60:.1f} /h")
c3.metric("Flow rate", f"{rate_per_min * 60:.1f} /h")
c4.metric("Flow time (no waiting)", f"{unloaded_flow_time(resources):g} min")

constraint = "capacity-constrained" if demand_per_min is None or demand_per_min >= process_capacity(resources) else "demand-constrained"
st.caption(f"The process is **{constraint}**: flow rate = min(demand, process capacity).")

st.subheader("Capacity per resource")
st.plotly_chart(capacity_figure(resources, demand_per_hour), width="stretch", key="capacity")

names = [r.name for r in resources]
u_left, u_right = st.columns(2)
with u_left:
    st.plotly_chart(
        utilization_figure(
            names,
            [utilization(r, rate_per_min) for r in resources],
            "Utilization (flow rate / capacity)",
        ),
        width="stretch",
        key="utilization",
    )
with u_right:
    if demand_per_min is not None:
        st.plotly_chart(
            utilization_figure(
                names,
                [implied_utilization(r, demand_per_min) for r in resources],
                "Implied utilization (demand / capacity)",
            ),
            width="stretch",
            key="implied_utilization",
        )
    else:
        st.info("Enter a demand to see implied utilization.")

# --- Little's Law --------------------------------------------------------------
st.subheader("Little's Law calculator — I = R × T")
st.caption("Use consistent units (e.g. flow rate in units/min and flow time in min).")

unknown = st.radio(
    "Solve for",
    ["Inventory (I)", "Flow rate (R)", "Flow time (T)"],
    horizontal=True,
)
k1, k2 = st.columns(2)
inputs: dict[str, float | None] = {"inventory": None, "flow_rate": None, "flow_time": None}
if unknown != "Inventory (I)":
    inputs["inventory"] = k1.number_input("Inventory I (units)", min_value=0.01, value=20.0)
if unknown != "Flow rate (R)":
    inputs["flow_rate"] = (k1 if unknown == "Inventory (I)" else k2).number_input(
        "Flow rate R (units/time)", min_value=0.01, value=4.0
    )
if unknown != "Flow time (T)":
    inputs["flow_time"] = k2.number_input("Flow time T (time)", min_value=0.01, value=5.0)

result = solve_littles_law(**inputs)
st.metric(unknown, f"{result:g}")
