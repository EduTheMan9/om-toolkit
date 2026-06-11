"""Plotly figure builders for the cellular manufacturing page. No Streamlit here."""
import plotly.graph_objects as go

# Entry categories for the clustered view (indices into the colorscale below).
_EMPTY, _VOID, _IN_CELL, _EXCEPTIONAL = 0, 1, 2, 3
_COLORS = ["#ffffff", "#d9d9d9", "#1f77b4", "crimson"]
# A discrete colorscale: each category index maps to one flat color band.
_SCALE = [
    [0.000, _COLORS[0]], [0.249, _COLORS[0]],
    [0.250, _COLORS[1]], [0.499, _COLORS[1]],
    [0.500, _COLORS[2]], [0.749, _COLORS[2]],
    [0.750, _COLORS[3]], [1.000, _COLORS[3]],
]


def _heatmap_layout(fig: go.Figure, title: str, n_rows: int) -> None:
    fig.update_layout(
        title=title,
        xaxis={"side": "top", "showgrid": False},
        yaxis={"autorange": "reversed", "showgrid": False},
        margin={"l": 10, "r": 10, "t": 70, "b": 10},
        height=140 + 40 * n_rows,
    )


def incidence_figure(
    matrix: list[list[int]], machine_names: list[str], part_names: list[str], title: str
) -> go.Figure:
    """Plain binary incidence matrix: blue = part visits machine."""
    fig = go.Figure(
        go.Heatmap(
            z=matrix, x=part_names, y=machine_names,
            zmin=0, zmax=1,
            colorscale=[[0, _COLORS[0]], [0.499, _COLORS[0]], [0.5, _COLORS[2]], [1, _COLORS[2]]],
            showscale=False, xgap=2, ygap=2,
            hovertemplate="%{y} × %{x}: %{z}<extra></extra>",
        )
    )
    _heatmap_layout(fig, title, len(matrix))
    return fig


def clustered_figure(
    matrix: list[list[int]],
    machine_names: list[str],
    part_names: list[str],
    machine_cells: list[int],
    part_cells: list[int],
    title: str,
) -> go.Figure:
    """Clustered matrix colored by what each entry does to grouping efficacy:
    blue = 1 inside its cell, red = exceptional element (1 outside every
    cell, a part travelling between cells), gray = void (0 inside a cell).
    All inputs must already be in display order."""
    categories, labels = [], []
    names = {_EMPTY: "", _VOID: "void", _IN_CELL: "in cell", _EXCEPTIONAL: "exceptional"}
    for i, row in enumerate(matrix):
        cat_row = []
        for j, entry in enumerate(row):
            same_cell = machine_cells[i] == part_cells[j]
            if entry == 1:
                cat_row.append(_IN_CELL if same_cell else _EXCEPTIONAL)
            else:
                cat_row.append(_VOID if same_cell else _EMPTY)
        categories.append(cat_row)
        labels.append([names[c] for c in cat_row])

    fig = go.Figure(
        go.Heatmap(
            z=categories, x=part_names, y=machine_names,
            zmin=0, zmax=3, colorscale=_SCALE,
            showscale=False, xgap=2, ygap=2,
            customdata=labels,
            hovertemplate="%{y} × %{x}: %{customdata}<extra></extra>",
        )
    )
    _heatmap_layout(fig, title, len(matrix))
    return fig
