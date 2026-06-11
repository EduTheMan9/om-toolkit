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

DISPATCH_EXAMPLES = {
    "Five jobs, one machine": {
        "description": "The worked example from the test suite. Row order = arrival "
        "order (FCFS). Watch EDD cut the number of late jobs.",
        "rows": [
            {"Job": "A", "Processing time": 6.0, "Due date": 8.0},
            {"Job": "B", "Processing time": 2.0, "Due date": 6.0},
            {"Job": "C", "Processing time": 8.0, "Due date": 18.0},
            {"Job": "D", "Processing time": 3.0, "Due date": 15.0},
            {"Job": "E", "Processing time": 9.0, "Due date": 23.0},
        ],
    },
    "Print shop (6 orders)": {
        "description": "Tight due dates early in the list - no rule saves every order.",
        "rows": [
            {"Job": "P1", "Processing time": 4.0, "Due date": 5.0},
            {"Job": "P2", "Processing time": 7.0, "Due date": 9.0},
            {"Job": "P3", "Processing time": 2.0, "Due date": 12.0},
            {"Job": "P4", "Processing time": 5.0, "Due date": 16.0},
            {"Job": "P5", "Processing time": 3.0, "Due date": 20.0},
            {"Job": "P6", "Processing time": 6.0, "Due date": 28.0},
        ],
    },
}

LOT_SIZING_EXAMPLES = {
    "Six-period demo": {
        "description": "The worked example from the test suite. Silver-Meal "
        "happens to find the optimum here - Wagner-Whitin guarantees it.",
        "setup_cost": 150.0,
        "holding_cost": 1.0,
        "demands": [50.0, 60.0, 90.0, 70.0, 30.0, 100.0],
    },
    "Lumpy demand (8 periods)": {
        "description": "Demand spikes with quiet periods in between - exactly "
        "where lot-for-lot wastes setups and EOQ-style fixed lots waste holding.",
        "setup_cost": 200.0,
        "holding_cost": 2.0,
        "demands": [10.0, 80.0, 0.0, 120.0, 5.0, 0.0, 90.0, 40.0],
    },
    "Cheap setups (6 periods)": {
        "description": "When setups are cheap relative to holding, ordering "
        "every period (lot-for-lot) is hard to beat.",
        "setup_cost": 30.0,
        "holding_cost": 3.0,
        "demands": [40.0, 50.0, 35.0, 60.0, 45.0, 55.0],
    },
}

CELLULAR_EXAMPLES = {
    "Two clean cells (4×5)": {
        "description": "The worked example from the test suite: ROC uncovers "
        "two near-perfect cells (one void, no exceptional elements).",
        "matrix": [
            [1, 0, 0, 1, 0],
            [0, 1, 1, 0, 1],
            [1, 0, 0, 1, 0],
            [0, 1, 1, 0, 0],
        ],
    },
    "Bottleneck machine (5×7)": {
        "description": "Machine M5 serves parts from two families - no "
        "reordering can avoid exceptional elements, only minimize them.",
        "matrix": [
            [1, 0, 0, 1, 0, 0, 1],
            [0, 1, 0, 0, 1, 0, 0],
            [1, 0, 0, 1, 0, 0, 0],
            [0, 1, 0, 0, 1, 1, 0],
            [0, 0, 1, 0, 0, 1, 1],
        ],
    },
    "Scrambled blocks (6×8)": {
        "description": "Three perfect cells hidden by the row order - watch "
        "ROC recover a block diagonal with grouping efficacy 1.",
        "matrix": [
            [0, 1, 0, 0, 0, 1, 0, 0],
            [1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 1, 0, 0, 1],
            [0, 1, 0, 0, 0, 1, 0, 0],
            [1, 0, 0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 1, 0, 0, 1],
        ],
    },
}

PRODUCTIVITY_EXAMPLES = {
    "Bakery, two weeks": {
        "description": "Last week is the worked example from the test suite "
        "(multifactor 5/3). This week output grew faster than input costs.",
        "output_values": (5000.0, 6000.0),
        "rows": [
            {"Input": "Labor", "Last period ($)": 1500.0, "This period ($)": 1600.0},
            {"Input": "Materials", "Last period ($)": 1000.0, "This period ($)": 1150.0},
            {"Input": "Overhead", "Last period ($)": 500.0, "This period ($)": 500.0},
        ],
    },
    "Automation trade-off": {
        "description": "A robot replaced most of the labor: labor productivity "
        "explodes, but MULTIFACTOR productivity falls - the machine costs more "
        "than the labor it saved.",
        "output_values": (8000.0, 8200.0),
        "rows": [
            {"Input": "Labor", "Last period ($)": 2000.0, "This period ($)": 800.0},
            {"Input": "Machines", "Last period ($)": 500.0, "This period ($)": 2200.0},
            {"Input": "Materials", "Last period ($)": 2000.0, "This period ($)": 2050.0},
        ],
    },
}

JOHNSON_EXAMPLES = {
    "Five jobs, two machines": {
        "description": "The worked example from the test suite (makespan 24).",
        "rows": [
            {"Job": "J1", "Machine 1 time": 3.0, "Machine 2 time": 6.0},
            {"Job": "J2", "Machine 1 time": 5.0, "Machine 2 time": 2.0},
            {"Job": "J3", "Machine 1 time": 1.0, "Machine 2 time": 2.0},
            {"Job": "J4", "Machine 1 time": 6.0, "Machine 2 time": 6.0},
            {"Job": "J5", "Machine 1 time": 7.0, "Machine 2 time": 5.0},
        ],
    },
    "Paint & dry (4 jobs)": {
        "description": "Painting booth feeds a drying oven.",
        "rows": [
            {"Job": "W1", "Machine 1 time": 4.0, "Machine 2 time": 7.0},
            {"Job": "W2", "Machine 1 time": 8.0, "Machine 2 time": 3.0},
            {"Job": "W3", "Machine 1 time": 5.0, "Machine 2 time": 5.0},
            {"Job": "W4", "Machine 1 time": 2.0, "Machine 2 time": 6.0},
        ],
    },
}
