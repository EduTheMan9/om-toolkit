"""Preset datasets so the app demos instantly.

Each example: editable-table rows (Task / Duration / Predecessors as a
comma-separated string) plus a default cycle time.
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
