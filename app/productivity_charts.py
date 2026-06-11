"""Plotly figure builders for the productivity page. No Streamlit here."""
import plotly.graph_objects as go


def change_figure(names: list[str], changes: list[float]) -> go.Figure:
    """Productivity change per factor: bars left of the zero line mean the
    factor got LESS productive (more input per unit of output)."""
    fig = go.Figure(
        go.Bar(
            y=names, x=[c * 100 for c in changes], orientation="h",
            marker_color=["crimson" if c < 0 else "#1f77b4" for c in changes],
            text=[f"{c:+.1%}" for c in changes],
            textposition="outside",
        )
    )
    fig.add_vline(x=0, line_color="black")
    spread = max(5.0, max(abs(c * 100) for c in changes) * 1.3)
    fig.update_layout(
        title="Productivity change by factor",
        xaxis={"title": "change (%)", "range": [-spread, spread]},
        yaxis={"autorange": "reversed"},
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
        height=120 + 45 * len(names),
    )
    return fig
