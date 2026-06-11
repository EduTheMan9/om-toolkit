import { describe, expect, it } from "vitest";
import { precedenceTraces } from "./diagram";

const TASKS = [
  { id: "A", duration: 5, predecessors: [] },
  { id: "B", duration: 3, predecessors: ["A"] },
  { id: "C", duration: 4, predecessors: ["A"] },
];
const COLUMNS = { A: 1, B: 2, C: 2 };

describe("precedenceTraces", () => {
  it("positions nodes by kilbridge column and spreads within a column", () => {
    const [, nodes] = precedenceTraces(TASKS, COLUMNS) as any[];
    expect(nodes.text).toEqual(["A", "B", "C"]);
    expect(nodes.x).toEqual([1, 2, 2]); // x = column
    expect(nodes.y[1]).not.toEqual(nodes.y[2]); // B and C spread apart
  });

  it("draws one edge per predecessor link, null-separated", () => {
    const [edges] = precedenceTraces(TASKS, COLUMNS) as any[];
    // A->B and A->C: 2 links x (from, to, null) = 6 points
    expect(edges.x).toHaveLength(6);
    expect(edges.x[2]).toBeNull();
  });
});
