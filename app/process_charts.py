"""Plotly figure builders for the process analysis page. No Streamlit here."""
import plotly.graph_objects as go

from core.process_analysis import Resource, bottleneck


def capacity_figure(
    resources: list[Resource], demand_per_hour: float | None = None
) -> go.Figure:
    """Capacity per resource in units/hour (processing times are minutes).
    The bottleneck bar is highlighted; the dashed line is demand."""
    bn = bottleneck(resources).name
    fig = go.Figure(
        go.Bar(
            x=[r.name for r in resources],
            y=[r.capacity * 60 for r in resources],
            marker_color=["crimson" if r.name == bn else "#1f77b4" for r in resources],
            text=[f"{r.capacity * 60:.1f}" for r in resources],
            textposition="outside",
        )
    )
    if demand_per_hour is not None:
        fig.add_hline(
            y=demand_per_hour, line_dash="dash", line_color="black",
            annotation_text="demand", annotation_position="top right",
        )
    fig.update_layout(
        yaxis_title="capacity (units/hour)",
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        height=380,
    )
    return fig


def utilization_figure(names: list[str], values: list[float], title: str) -> go.Figure:
    """Horizontal utilization bars; anything past the 100% line is overload."""
    fig = go.Figure(
        go.Bar(
            y=names, x=[v * 100 for v in values], orientation="h",
            marker_color=["crimson" if v > 1 else "#1f77b4" for v in values],
            text=[f"{v:.0%}" for v in values],
            textposition="outside",
        )
    )
    fig.add_vline(x=100, line_dash="dash", line_color="black")
    fig.update_layout(
        title=title,
        xaxis={"title": "%", "range": [0, max(110, max(v * 100 for v in values) * 1.15)]},
        yaxis={"autorange": "reversed"},
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=90 + 45 * len(names),
    )
    return fig
