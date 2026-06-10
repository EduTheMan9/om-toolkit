"""Preset datasets so the app demos instantly.

Line balancing examples: editable-table rows (Task / Duration / Predecessors
as a comma-separated string) plus a default cycle time.
Process analysis examples: resource rows plus a default demand in units/hour.
"""

EXAMPLES = {
    "Demo line (6 tasks)": {
        "description": "The worked example from the test suite. Durations in minutes.",
        "cycle_time": 10.0,
        "rows": [
            {"Task": "A", "Duration": 5.0, "Predecessors": ""},
            {"Task": "B", "Duration": 3.0, "Predecessors": "A"},
            {"Task": "C", "Duration": 4.0, "Predecessors": "A"},
            {"Task": "D", "Duration": 2.0, "Predecessors": "B"},
            {"Task": "E", "Duration": 6.0, "Predecessors": "C"},
            {"Task": "F", "Duration": 4.0, "Predecessors": "D, E"},
        ],
    },
    "Appliance assembly (9 tasks)": {
        "description": "A two-branch line that merges at final assembly. Durations in minutes.",
        "cycle_time": 11.0,
        "rows": [
            {"Task": "A", "Duration": 4.0, "Predecessors": ""},
            {"Task": "B", "Duration": 5.0, "Predecessors": "A"},
            {"Task": "C", "Duration": 2.0, "Predecessors": "A"},
            {"Task": "D", "Duration": 6.0, "Predecessors": "B"},
            {"Task": "E", "Duration": 3.0, "Predecessors": "C"},
            {"Task": "F", "Duration": 5.0, "Predecessors": "C"},
            {"Task": "G", "Duration": 7.0, "Predecessors": "D, E"},
            {"Task": "H", "Duration": 4.0, "Predecessors": "F"},
            {"Task": "I", "Duration": 6.0, "Predecessors": "G, H"},
        ],
    },
    "Small workshop (4 tasks)": {
        "description": "Minimal starter example - good for trying your own edits. Durations in minutes.",
        "cycle_time": 7.0,
        "rows": [
            {"Task": "A", "Duration": 3.0, "Predecessors": ""},
            {"Task": "B", "Duration": 4.0, "Predecessors": "A"},
            {"Task": "C", "Duration": 2.0, "Predecessors": "A"},
            {"Task": "D", "Duration": 5.0, "Predecessors": "B, C"},
        ],
    },
}

PROCESS_EXAMPLES = {
    "Sandwich line": {
        "description": "Four-step sandwich shop. Toasting is the bottleneck "
        "even though making the sandwich takes longer, because making has two workers.",
        "demand_per_hour": 35.0,
        "rows": [
            {"Resource": "Take order", "Processing time (min)": 1.5, "Servers": 1},
            {"Resource": "Make sandwich", "Processing time (min)": 3.0, "Servers": 2},
            {"Resource": "Toast", "Processing time (min)": 2.0, "Servers": 1},
            {"Resource": "Checkout", "Processing time (min)": 1.0, "Servers": 1},
        ],
    },
    "Health clinic": {
        "description": "Demand exceeds the nurses' capacity - watch implied "
        "utilization go past 100%.",
        "demand_per_hour": 10.0,
        "rows": [
            {"Resource": "Reception", "Processing time (min)": 5.0, "Servers": 1},
            {"Resource": "Nurse triage", "Processing time (min)": 15.0, "Servers": 2},
            {"Resource": "Doctor consult", "Processing time (min)": 20.0, "Servers": 3},
        ],
    },
    "Three-step demo": {
        "description": "The worked example from the test suite.",
        "demand_per_hour": 9.0,
        "rows": [
            {"Resource": "A", "Processing time (min)": 10.0, "Servers": 2},
            {"Resource": "B", "Processing time (min)": 6.0, "Servers": 1},
            {"Resource": "C", "Processing time (min)": 4.0, "Servers": 1},
        ],
    },
}
