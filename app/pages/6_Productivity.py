import pandas as pd
import streamlit as st

from app.examples import PRODUCTIVITY_EXAMPLES
from app.productivity_charts import change_figure
from core.productivity import (
    multifactor_productivity,
    productivity_change,
    single_factor_productivity,
)

st.set_page_config(page_title="Productivity — OM Toolkit", page_icon="📈", layout="wide")
st.title("📈 Productivity Metrics")

# --- Single-factor calculator -----------------------------------------------------
st.subheader("Single-factor calculator")
st.caption(
    "Output per unit of ONE input — any units you like (units per labor-hour, "
    "titles per clerk, € per kWh)."
)
c1, c2, c3 = st.columns(3)
output_qty = c1.number_input("Output (units)", min_value=0.0, value=500.0)
input_qty = c2.number_input("Input (e.g. labor-hours)", min_value=0.01, value=200.0)
c3.metric("Single-factor productivity", f"{single_factor_productivity(output_qty, input_qty):g}")

st.divider()

# --- Two-period multifactor comparison --------------------------------------------
st.subheader("Two-period comparison")
example_name = st.selectbox("Load an example", list(PRODUCTIVITY_EXAMPLES))
example = PRODUCTIVITY_EXAMPLES[example_name]
st.caption(
    example["description"]
    + " All figures in money so the inputs can be added together."
)

left, right = st.columns([3, 2])
with left:
    st.markdown("**Input costs**")
    edited = st.data_editor(
        pd.DataFrame(example["rows"]),
        num_rows="dynamic",
        width="stretch",
        key=f"inputs_{example_name}",
        column_config={
            "Input": st.column_config.TextColumn(required=True),
            "Last period ($)": st.column_config.NumberColumn(min_value=0.0),
            "This period ($)": st.column_config.NumberColumn(min_value=0.0),
        },
    )
with right:
    st.markdown("**Output value**")
    prev_output = st.number_input(
        "Last period ($)", min_value=0.0,
        value=example["output_values"][0], key=f"prev_{example_name}",
    )
    cur_output = st.number_input(
        "This period ($)", min_value=0.0,
        value=example["output_values"][1], key=f"cur_{example_name}",
    )


def _cost(row: dict, column: str) -> float:
    value = row.get(column)
    return 0.0 if value is None or pd.isna(value) else float(value)


factors: dict[str, tuple[float, float]] = {}
for record in edited.to_dict("records"):
    name = str(record.get("Input") or "").strip()
    if not name:
        continue  # ignore blank editor rows
    factors[name] = (_cost(record, "Last period ($)"), _cost(record, "This period ($)"))

prev_costs = {name: costs[0] for name, costs in factors.items()}
cur_costs = {name: costs[1] for name, costs in factors.items()}
try:
    prev_mfp = multifactor_productivity(prev_output, prev_costs)
    cur_mfp = multifactor_productivity(cur_output, cur_costs)
except ValueError as err:
    st.error(str(err))
    st.stop()

# Per-factor single-factor productivity ($ output per $ of that input);
# a factor with zero cost in either period has no defined ratio or change.
names, changes = [], []
table_rows = []
for name, (prev_cost, cur_cost) in factors.items():
    if prev_cost > 0 and cur_cost > 0:
        prev_p = single_factor_productivity(prev_output, prev_cost)
        cur_p = single_factor_productivity(cur_output, cur_cost)
        change = productivity_change(prev_p, cur_p)
        names.append(name)
        changes.append(change)
        table_rows.append((name, f"{prev_p:.3f}", f"{cur_p:.3f}", f"{change:+.1%}"))
    else:
        table_rows.append((name, "—", "—", "—"))

mfp_change = productivity_change(prev_mfp, cur_mfp)
names.append("Multifactor (all inputs)")
changes.append(mfp_change)
table_rows.append(
    ("Multifactor (all inputs)", f"{prev_mfp:.3f}", f"{cur_mfp:.3f}", f"{mfp_change:+.1%}")
)

m1, m2, m3 = st.columns(3)
m1.metric("Multifactor, last period", f"{prev_mfp:.3f}")
m2.metric("Multifactor, this period", f"{cur_mfp:.3f}")
m3.metric("Change", f"{mfp_change:+.1%}")

comparison = pd.DataFrame(
    [row[1:] for row in table_rows],
    columns=["Last period", "This period", "Change"],
    index=[row[0] for row in table_rows],
)
st.dataframe(comparison, width="stretch", key="comparison")
st.caption(
    "Single-factor rows divide output value by ONE input's cost, so a factor "
    "can look great while the others absorb the load. The multifactor row "
    "divides by ALL input costs together — that is the one that says whether "
    "the operation as a whole got more productive."
)

st.plotly_chart(change_figure(names, changes), width="stretch", key="changes")
