import type { DispatchJob, JohnsonJob } from "../../lib/urlState";

export const DISPATCH_PRESETS: Record<string, DispatchJob[]> = {
  "Five-job demo": [
    { id: "A", processingTime: 6, dueDate: 8, weight: 1 },
    { id: "B", processingTime: 2, dueDate: 6, weight: 1 },
    { id: "C", processingTime: 8, dueDate: 18, weight: 1 },
    { id: "D", processingTime: 3, dueDate: 15, weight: 1 },
    { id: "E", processingTime: 9, dueDate: 23, weight: 1 },
  ],
  // the classic counterexample where EDD is NOT optimal for total tardiness
  "EDD beaten by the DP": [
    { id: "A", processingTime: 4, dueDate: 4, weight: 1 },
    { id: "B", processingTime: 3, dueDate: 5, weight: 1 },
    { id: "C", processingTime: 2, dueDate: 6, weight: 1 },
  ],
  // weighted: the big-but-important job C (weight 4) jumps ahead under WSPT
  // even though SPT would bury it behind the short jobs.
  "Weighted jobs (WSPT)": [
    { id: "A", processingTime: 6, dueDate: 8, weight: 1 },
    { id: "B", processingTime: 2, dueDate: 6, weight: 2 },
    { id: "C", processingTime: 8, dueDate: 18, weight: 4 },
    { id: "D", processingTime: 3, dueDate: 15, weight: 1 },
    { id: "E", processingTime: 9, dueDate: 23, weight: 3 },
  ],
};

export const JOHNSON_PRESETS: Record<string, JohnsonJob[]> = {
  "Five-job flow shop": [
    { id: "J1", timeM1: 3, timeM2: 6 },
    { id: "J2", timeM1: 5, timeM2: 2 },
    { id: "J3", timeM1: 1, timeM2: 2 },
    { id: "J4", timeM1: 6, timeM2: 6 },
    { id: "J5", timeM1: 7, timeM2: 5 },
  ],
  "Machine 2 is the slow side": [
    { id: "P1", timeM1: 2, timeM2: 7 },
    { id: "P2", timeM1: 4, timeM2: 6 },
    { id: "P3", timeM1: 3, timeM2: 8 },
    { id: "P4", timeM1: 6, timeM2: 5 },
  ],
};
