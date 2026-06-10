import streamlit as st

st.set_page_config(page_title="OM Toolkit", page_icon="🏭", layout="wide")

st.title("🏭 OM Toolkit")
st.write(
    "Interactive solvers for the core Operations Management methods, "
    "built for Industrial & Management Engineering students."
)

st.page_link("pages/1_Line_Balancing.py", label="Assembly Line Balancing", icon="⚖️")

st.subheader("Roadmap")
st.markdown(
    """
| Module | Status |
|---|---|
| Assembly Line Balancing | ✅ available |
| Process analysis & bottleneck (capacity, utilization, Little's Law) | planned |
| Scheduling (Johnson's rule, dispatching rules, Gantt charts) | planned |
| MRP & lot-sizing (EOQ, lot-for-lot, Silver–Meal, Wagner–Whitin) | planned |
| Cellular manufacturing (rank order clustering) | planned |
| Productivity metrics | planned |
"""
)
