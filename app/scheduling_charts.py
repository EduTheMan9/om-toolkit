"""Plotly Gantt builders for the scheduling page. No Streamlit here."""
import plotly.graph_objects as go

from core.scheduling import ScheduledJob, TwoMachineSchedule


def _add_bar(fig: go.Figure, row: str, s: ScheduledJob, color: str) -> None:
    fig.add_trace(
        go.Bar(
            y=[row], x=[s.end - s.start], base=[s.start], orientation="h",
            marker_color=color,
            marker_line={"color": "white", "width": 1},
            text=f"<b>{s.id}</b>", textposition="inside", insidetextanchor="middle",
            hovertext=f"{s.id}: {s.start:g} to {s.end:g}",
            hoverinfo="text",
            showlegend=False,
        )
    )


def rules_gantt(
    schedules: dict[str, list[ScheduledJob]], due_dates: dict[str, float]
) -> go.Figure:
    """One Gantt row per dispatching rule; tardy jobs colored red."""
    fig = go.Figure()
    for rule, schedule in schedules.items():
        for s in schedule:
            tardy = s.end > due_dates[s.id]
            _add_bar(fig, rule, s, "crimson" if tardy else "#1f77b4")
    fig.update_layout(
        barmode="overlay",
        xaxis_title="time (red = job finishes after its due date)",
        yaxis={"autorange": "reversed"},
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        height=110 + 45 * len(schedules),
    )
    return fig


def two_machine_gantt(schedule: TwoMachineSchedule) -> go.Figure:
    """Machine 1 and machine 2 rows; gaps on machine 2 are idle time."""
    fig = go.Figure()
    for s in schedule.machine1:
        _add_bar(fig, "Machine 1", s, "#1f77b4")
    for s in schedule.machine2:
        _add_bar(fig, "Machine 2", s, "#2ca02c")
    fig.add_vline(
        x=schedule.makespan, line_dash="dash", line_color="black",
        annotation_text=f"makespan = {schedule.makespan:g}",
        annotation_position="top",
    )
    fig.update_layout(
        barmode="overlay",
        xaxis_title="time",
        yaxis={"autorange": "reversed"},
        margin={"l": 10, "r": 10, "t": 30, "b": 10},
        height=220,
    )
    return fig
