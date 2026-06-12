import { describe, expect, it } from "vitest";
import { clusteredTrace, incidenceTrace, names, partDisplayOrder, reorder } from "./charts";

// Hand-traced Example A (tests/test_cells.py)
const MATRIX_A = [
  [1, 0, 0, 1, 0],
  [0, 1, 1, 0, 1],
  [1, 0, 0, 1, 0],
  [0, 1, 1, 0, 0],
];

describe("names", () => {
  it("auto-names machines and parts from 1", () => {
    expect(names("M", 3)).toEqual(["M1", "M2", "M3"]);
  });
});

describe("reorder", () => {
  it("applies the hand-traced ROC orders for example A", () => {
    expect(reorder(MATRIX_A, [0, 2, 1, 3], [0, 3, 1, 2, 4])).toEqual([
      [1, 1, 0, 0, 0],
      [1, 1, 0, 0, 0],
      [0, 0, 1, 1, 1],
      [0, 0, 1, 1, 0],
    ]);
  });
});

describe("partDisplayOrder", () => {
  it("groups part columns by cell, keeping relative ROC order", () => {
    // ROC order [2,0,1] with cells (by original index) [0,1,1]:
    // P1 (cell 0) first, then P3, P2 keep their ROC relative order
    expect(partDisplayOrder([2, 0, 1], [0, 1, 1])).toEqual([0, 2, 1]);
  });
});

describe("incidenceTrace", () => {
  it("passes the binary matrix through as heatmap z", () => {
    const trace = incidenceTrace(MATRIX_A, names("M", 4), names("P", 5)) as any;
    expect(trace.z).toEqual(MATRIX_A);
    expect(trace.y).toEqual(["M1", "M2", "M3", "M4"]);
  });
});

describe("clusteredTrace", () => {
  it("categorizes entries: empty 0, void 1, in-cell 2, exceptional 3", () => {
    // Example A in display order: machines M1,M3,M2,M4 / parts P1,P4,P2,P3,P5
    const ordered = reorder(MATRIX_A, [0, 2, 1, 3], [0, 3, 1, 2, 4]);
    const trace = clusteredTrace(
      ordered,
      ["M1", "M3", "M2", "M4"],
      ["P1", "P4", "P2", "P3", "P5"],
      [0, 0, 1, 1],
      [0, 0, 1, 1, 1],
    ) as any;
    // M4 row: two empties, two in-cell 1s, and the M4-P5 void
    expect(trace.z[3]).toEqual([0, 0, 2, 2, 1]);
    expect(trace.customdata[3]).toEqual(["", "", "in cell", "in cell", "void"]);
  });
});
