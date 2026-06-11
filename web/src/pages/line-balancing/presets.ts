import type { BalancingInputs } from "../../lib/urlState";

export const BALANCING_PRESETS: Record<string, BalancingInputs> = {
  "Six-task demo": {
    tasks: [
      { id: "A", duration: 5, predecessors: [] },
      { id: "B", duration: 3, predecessors: ["A"] },
      { id: "C", duration: 4, predecessors: ["A"] },
      { id: "D", duration: 2, predecessors: ["B"] },
      { id: "E", duration: 6, predecessors: ["C"] },
      { id: "F", duration: 4, predecessors: ["D", "E"] },
    ],
    cycleTime: 10,
    availableTime: null,
    demand: null,
  },
  "From demand (480 min, 70 units)": {
    tasks: [
      { id: "A", duration: 3, predecessors: [] },
      { id: "B", duration: 4, predecessors: ["A"] },
      { id: "C", duration: 2, predecessors: ["A"] },
      { id: "D", duration: 5, predecessors: ["B", "C"] },
      { id: "E", duration: 3, predecessors: ["D"] },
    ],
    cycleTime: null,
    availableTime: 480,
    demand: 70,
  },
};
