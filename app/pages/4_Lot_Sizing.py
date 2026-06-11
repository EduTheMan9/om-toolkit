import pandas as pd
import streamlit as st

from app.examples import LOT_SIZING_EXAMPLES
from app.lot_charts import eoq_cost_figure, plan_figure
from core.lot_sizing import (
    economic_order_quantity,
    evaluate_plan,
    lot_for_lot,
    silver_meal,
    validate_inputs,
    wagner_whitin,
)

st.set_page_config(page_title="Lot Sizing — OM Toolkit", page_icon="📦", layout="wide")
st.title("📦 MRP & Lot Sizing")

eoq_tab, dynamic_tab = st.tabs(
    ["Constant demand — EOQ", "Period-by-period demand — dynamic lot sizing"]
)

# --- Tab 1: EOQ ----------------------------------------------------------------
with eoq_tab:
    st.caption(
        "Constant, continuous demand. Use the same time basis for all three "
        "inputs (e.g. per year)."
    )
    c1, c2, c3 = st.columns(3)
    demand = c1.number_input("Demand D (units/period)", min_value=0.01, value=1200.0)
    ordering_cost = c2.number_input("Ordering cost S (per order)", min_value=0.01, value=100.0)
    holding_cost = c3.number_input(
        "Holding cost H (per unit per period)", min_value=0.01, value=6.0
    )

    result = economic_order_quantity(demand, ordering_cost, holding_cost)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Optimal quantity Q*", f"{result.quantity:.1f}")
    m2.metric("Orders per period", f"{result.orders_per_period:.2f}")
    m3.metric("Time between orders", f"{result.time_between_orders:.3f} periods")
    m4.metric("Total relevant cost", f"{result.total_cost:.2f}")

    st.plotly_chart(
        eoq_cost_figure(demand, ordering_cost, holding_cost, result),
        width="stretch",
        key="eoq_curve",
    )
    st.caption(
        f"At Q* the two costs are equal — ordering {result.ordering_cost_total:.2f} "
        f"= holding {result.holding_cost_total:.2f}. That crossing is not a "
        "coincidence: it is the first-order condition of minimizing "
        "TC = (D/Q)S + (Q/2)H. The total curve is flat near Q*, so rounding "
        "to a convenient lot size costs little."
    )

# --- Tab 2: dynamic lot sizing ---------------------------------------------------
with dynamic_tab:
    example_name = st.selectbox("Load an example", list(LOT_SIZING_EXAMPLES))
    example = LOT_SIZING_EXAMPLES[example_name]
    st.caption(
        example["description"]
        + " Orders arrive at the start of a period; holding is charged on "
        "end-of-period inventory."
    )

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Demand per period")
        edited = st.data_editor(
            pd.DataFrame(
                {
                    "Period": list(range(1, len(example["demands"]) + 1)),
                    "Demand": example["demands"],
                }
            ),
            num_rows="dynamic",
            width="stretch",
            key=f"demands_{example_name}",
            column_config={
                "Period": st.column_config.NumberColumn(disabled=True),
                "Demand": st.column_config.NumberColumn(min_value=0.0),
            },
        )
    with right:
        st.subheader("Costs")
        setup_cost = st.number_input(
            "Setup cost S (per order)", min_value=0.01,
            value=float(example["setup_cost"]), key=f"setup_{example_name}",
        )
        holding_cost = st.number_input(
            "Holding cost h (per unit per period)", min_value=0.01,
            value=float(example["holding_cost"]), key=f"holding_{example_name}",
        )

    demands = [
        0.0 if pd.isna(r["Demand"]) else float(r["Demand"])
        for r in edited.to_dict("records")
    ]
    try:
        validate_inputs(demands, setup_cost, holding_cost)
    except ValueError as err:
        st.error(str(err))
        st.stop()

    plans = {
        "Lot-for-lot": lot_for_lot(demands, setup_cost, holding_cost),
        "Silver–Meal": silver_meal(demands, setup_cost, holding_cost),
        "Wagner–Whitin": wagner_whitin(demands, setup_cost, holding_cost),
    }
    costs = {
        name: evaluate_plan(demands, orders, setup_cost, holding_cost)
        for name, orders in plans.items()
    }

    comparison = pd.DataFrame(
        {
            "Orders": [
                ", ".join(f"{q:g}" for q in orders) for orders in plans.values()
            ],
            "Setups": [c["setups"] for c in costs.values()],
            "Setup cost": [f"{c['setup_cost']:g}" for c in costs.values()],
            "Holding cost": [f"{c['holding_cost']:g}" for c in costs.values()],
            "Total cost": [f"{c['total_cost']:g}" for c in costs.values()],
        },
        index=list(plans),
    )
    st.dataframe(comparison, width="stretch", key="lot_comparison")

    ww_total = costs["Wagner–Whitin"]["total_cost"]
    sm_total = costs["Silver–Meal"]["total_cost"]
    gap = (
        "matches the optimum on this instance"
        if sm_total == ww_total
        else f"is {(sm_total / ww_total - 1):.1%} above the optimum here"
    )
    st.caption(
        "Each lot trades one setup against the holding cost of carrying future "
        "demand. Wagner–Whitin (dynamic programming) is provably optimal; "
        f"Silver–Meal is a myopic heuristic that {gap}. Lot-for-lot is the "
        "zero-inventory baseline MRP systems default to."
    )

    for name, orders in plans.items():
        st.plotly_chart(
            plan_figure(
                demands, orders, costs[name]["ending_inventory"],
                f"{name} — total cost {costs[name]['total_cost']:g}",
            ),
            width="stretch",
            key=f"plan_{name}",
        )
