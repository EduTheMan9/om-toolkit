"""Plotly figure builders for the line balancing page.

No Streamlit imports here: these take core objects and return figures,
so they stay testable and reusable.
"""
from collections import defaultdict

import plotly.graph_objects as go

from core.line_balancing import Station, Task, kilbridge_columns


def precedence_figure(tasks: list[Task]) -> go.Figure:
    """Left-to-right precedence diagram. X = Kilbridge column (precedence
    depth), Y spreads tasks within a column."""
    columns = kilbridge_columns(tasks)
    by_column: dict[int, list[Task]] = defaultdict(list)
    for t in sorted(tasks, key=lambda t: t.id):
        by_column[columns[t.id]].append(t)

    pos: dict[str, tuple[float, float]] = {}
    for col, col_tasks in by_column.items():
        n = len(col_tasks)
        for i, t in enumerate(col_tasks):
            pos[t.id] = (float(col), (n - 1) / 2 - i)

    fig = go.Figure()
    for t in tasks:
        for p in t.predecessors:
            (x0, y0), (x1, y1) = pos[p], pos[t.id]
            fig.add_trace(
                go.Scatter(
                    x=[x0, x1], y=[y0, y1], mode="lines",
                    line={"color": "#b0b0b0", "width": 1.5},
                    hoverinfo="skip", showlegend=False,
                )
            )
    fig.add_trace(
        go.Scatter(
            x=[pos[t.id][0] for t in tasks],
            y=[pos[t.id][1] for t in tasks],
            mode="markers+text",
            marker={"size": 52, "color": "#1f77b4"},
            text=[f"<b>{t.id}</b><br>{t.duration:g}" for t in tasks],
            textfont={"color": "white", "size": 12},
            textposition="middle center",
            hovertext=[
                f"Task {t.id} - duration {t.duration:g}"
                + (f"<br>after: {', '.join(t.predecessors)}" if t.predecessors else "")
                for t in tasks
            ],
            hoverinfo="text",
            showlegend=False,
        )
    )
    fig.update_layout(
        xaxis={"visible": False}, yaxis={"visible": False},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        height=120 + 70 * max(len(v) for v in by_column.values()),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def stations_figure(stations: list[Station], cycle_time: float) -> go.Figure:
    """One horizontal stacked bar per station; the dashed line is the cycle
    time, so the gap to it is each station's idle time."""
    fig = go.Figure()
    for s in stations:
        offset = 0.0
        for t in s.tasks:
            fig.add_trace(
                go.Bar(
                    y=[f"Station {s.index}"], x=[t.duration],
                    orientation="h",
                    text=f"<b>{t.id}</b> ({t.duration:g})",
                    textposition="inside", insidetextanchor="middle",
                    hovertext=f"Task {t.id}: {offset:g} to {offset + t.duration:g}",
                    hoverinfo="text",
                    showlegend=False,
                )
            )
            offset += t.duration
    fig.add_vline(x=cycle_time, line_dash="dash", line_color="crimson",
                  annotation_text="cycle time", annotation_position="top")
    fig.update_layout(
        barmode="stack",
        yaxis={"autorange": "reversed"},
        xaxis={"title": "time", "range": [0, cycle_time * 1.08]},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        height=90 + 45 * len(stations),
    )
    return fig
