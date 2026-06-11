"""Plotly figure builders for the lot sizing page. No Streamlit here."""
import plotly.graph_objects as go

from core.lot_sizing import EOQResult


def eoq_cost_figure(
    demand: float, ordering_cost: float, holding_cost: float, result: EOQResult
) -> go.Figure:
    """Ordering cost falls as 1/Q, holding cost rises linearly; their sum is
    minimized exactly where the curves cross — that crossing is Q*."""
    n_points = 200
    q_max = result.quantity * 3
    quantities = [q_max * (i + 1) / n_points for i in range(n_points)]
    ordering = [(demand / q) * ordering_cost for q in quantities]
    holding = [(q / 2) * holding_cost for q in quantities]

    fig = go.Figure()
    fig.add_scatter(x=quantities, y=ordering, name="Ordering (D/Q)·S", line_color="#1f77b4")
    fig.add_scatter(x=quantities, y=holding, name="Holding (Q/2)·H", line_color="#ff7f0e")
    fig.add_scatter(
        x=quantities, y=[o + h for o, h in zip(ordering, holding)],
        name="Total", line_color="crimson", line_width=3,
    )
    fig.add_vline(
        x=result.quantity, line_dash="dash", line_color="black",
        annotation_text=f"Q* = {result.quantity:.1f}", annotation_position="top right",
    )
    fig.update_layout(
        xaxis_title="order quantity Q",
        yaxis_title="cost per period",
        # Total cost is flat near Q*, so cap the y-axis: the interesting region
        # is around the minimum, not the 1/Q blow-up at tiny Q.
        yaxis_range=[0, result.total_cost * 3],
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        height=420,
    )
    return fig


def plan_figure(
    demands: list[float], orders: list[float], ending_inventory: list[float], title: str
) -> go.Figure:
    """One method's plan: demand vs order bars per period, with the ending
    inventory line showing what each oversized order leaves behind to carry."""
    periods = list(range(1, len(demands) + 1))
    fig = go.Figure()
    fig.add_bar(x=periods, y=demands, name="Demand", marker_color="#1f77b4")
    fig.add_bar(x=periods, y=orders, name="Order", marker_color="#ff7f0e")
    fig.add_scatter(
        x=periods, y=ending_inventory, name="Ending inventory",
        mode="lines+markers", line_color="crimson",
    )
    fig.update_layout(
        title=title,
        barmode="group",
        xaxis={"title": "period", "dtick": 1},
        yaxis_title="units",
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=330,
    )
    return fig
