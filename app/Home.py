import streamlit as st

st.set_page_config(page_title="OM Toolkit", page_icon="🏭", layout="wide")

st.title("🏭 OM Toolkit")
st.write(
    "Interactive solvers for the core Operations Management methods, "
    "built for Industrial & Management Engineering students."
)

st.page_link("pages/1_Line_Balancing.py", label="Assembly Line Balancing", icon="⚖️")
st.page_link("pages/2_Process_Analysis.py", label="Process Analysis & Bottleneck", icon="🔍")
st.page_link("pages/3_Scheduling.py", label="Scheduling", icon="📅")
st.page_link("pages/4_Lot_Sizing.py", label="MRP & Lot Sizing", icon="📦")
st.page_link("pages/5_Cellular.py", label="Cellular Manufacturing", icon="🔳")

st.subheader("Roadmap")
st.markdown(
    """
| Module | Status |
|---|---|
| Assembly Line Balancing | ✅ available |
| Process analysis & bottleneck (capacity, utilization, Little's Law) | ✅ available |
| Scheduling (Johnson's rule, dispatching rules, Gantt charts) | ✅ available |
| MRP & lot-sizing (EOQ, lot-for-lot, Silver–Meal, Wagner–Whitin) | ✅ available |
| Cellular manufacturing (rank order clustering) | ✅ available |
| Productivity metrics | planned |
"""
)
