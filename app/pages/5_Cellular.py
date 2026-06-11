import pandas as pd
import streamlit as st

from app.cell_charts import clustered_figure, incidence_figure
from app.examples import CELLULAR_EXAMPLES
from core.cellular import (
    MAX_PARTITION_MACHINES,
    evaluate_cells,
    find_best_cells,
    rank_order_clustering,
    reorder_matrix,
    validate_matrix,
)

st.set_page_config(page_title="Cellular — OM Toolkit", page_icon="🔳", layout="wide")
st.title("🔳 Cellular Manufacturing — Rank Order Clustering")

st.caption(
    "Tick a cell when the part (column) visits the machine (row). ROC sorts "
    "rows and columns by their binary values until the 1s gather into "
    "diagonal blocks — those blocks are your manufacturing cells."
)

example_name = st.selectbox("Load an example", list(CELLULAR_EXAMPLES))
example = CELLULAR_EXAMPLES[example_name]
st.caption(example["description"])

n_parts = st.number_input(
    "Number of parts", min_value=1, max_value=30,
    value=len(example["matrix"][0]), key=f"parts_{example_name}",
)
part_names = [f"P{j + 1}" for j in range(int(n_parts))]

rows = [
    {"Machine": f"M{i + 1}", **{p: bool(row[j]) if j < len(row) else False
                                for j, p in enumerate(part_names)}}
    for i, row in enumerate(example["matrix"])
]
edited = st.data_editor(
    pd.DataFrame(rows),
    num_rows="dynamic",
    width="stretch",
    key=f"matrix_{example_name}_{n_parts}",
    column_config={
        "Machine": st.column_config.TextColumn(required=True),
        **{p: st.column_config.CheckboxColumn(default=False) for p in part_names},
    },
)

machine_names = []
matrix = []
for record in edited.to_dict("records"):
    name = str(record.get("Machine") or "").strip()
    if not name:
        continue  # ignore blank editor rows
    machine_names.append(name)
    matrix.append([1 if record.get(p) else 0 for p in part_names])

try:
    validate_matrix(matrix)
except ValueError as err:
    st.error(str(err))
    st.stop()

roc = rank_order_clustering(matrix)

# --- Cells and metrics ----------------------------------------------------------
if len(matrix) <= MAX_PARTITION_MACHINES:
    machine_cells, part_cells = find_best_cells(matrix, roc.row_order)
    metrics = evaluate_cells(matrix, machine_cells, part_cells)
    n_cells = max(machine_cells) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cells", n_cells)
    c2.metric("Exceptional elements", metrics["exceptional"])
    c3.metric("Voids", metrics["voids"])
    c4.metric("Grouping efficacy", f"{metrics['grouping_efficacy']:.3f}")
    st.caption(
        "Grouping efficacy μ = (e − exceptional) / (e + voids), where e is "
        f"the {metrics['total_ones']} ones in the matrix. Exceptional "
        "elements are parts forced to travel between cells; voids are idle "
        "machine–part pairings inside a cell. μ = 1 is a perfect block "
        "diagonal."
    )
else:
    machine_cells = part_cells = None
    st.info(
        f"Cell search is shown up to {MAX_PARTITION_MACHINES} machines — it "
        "tries every consecutive split of the machine list, which doubles "
        "with each machine added. The ROC reordering below still works."
    )

# --- Before / after -------------------------------------------------------------
before, after = st.columns(2)
with before:
    st.plotly_chart(
        incidence_figure(matrix, machine_names, part_names[: len(matrix[0])], "Original matrix"),
        width="stretch",
        key="before",
    )
with after:
    if machine_cells is None:
        ordered = reorder_matrix(matrix, roc.row_order, roc.col_order)
        st.plotly_chart(
            incidence_figure(
                ordered,
                [machine_names[i] for i in roc.row_order],
                [part_names[j] for j in roc.col_order],
                "After ROC",
            ),
            width="stretch",
            key="after",
        )
    else:
        # Group part columns by cell (keeping ROC relative order) so each
        # cell shows as one contiguous block.
        display_cols = sorted(roc.col_order, key=lambda j: part_cells[j])
        ordered = reorder_matrix(matrix, roc.row_order, display_cols)
        st.plotly_chart(
            clustered_figure(
                ordered,
                [machine_names[i] for i in roc.row_order],
                [part_names[j] for j in display_cols],
                [machine_cells[i] for i in roc.row_order],
                [part_cells[j] for j in display_cols],
                "After ROC, grouped into cells",
            ),
            width="stretch",
            key="after",
        )

# --- Cell composition -----------------------------------------------------------
if machine_cells is not None:
    st.subheader("Cell composition")
    composition = pd.DataFrame(
        {
            "Machines": [
                ", ".join(
                    machine_names[i]
                    for i in roc.row_order
                    if machine_cells[i] == cell
                )
                for cell in range(n_cells)
            ],
            "Parts": [
                ", ".join(
                    part_names[j]
                    for j in roc.col_order
                    if part_cells[j] == cell
                )
                for cell in range(n_cells)
            ],
        },
        index=[f"Cell {cell + 1}" for cell in range(n_cells)],
    )
    st.dataframe(composition, width="stretch", key="composition")
    st.caption(
        "ROC itself only reorders the matrix; the cells come from trying "
        "every consecutive split of the reordered machine list and keeping "
        "the one with the highest grouping efficacy (each part joins the "
        "cell where it has the most operations; ties go to the earlier cell)."
    )
