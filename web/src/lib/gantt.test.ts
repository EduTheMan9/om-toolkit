import { describe, expect, it } from "vitest";
import { ganttTraces } from "./gantt";

describe("ganttTraces", () => {
  it("converts scheduled jobs to positioned horizontal bars", () => {
    const traces = ganttTraces([
      {
        label: "M1",
        jobs: [
          { id: "A", start: 0, end: 6 },
          { id: "B", start: 6, end: 8 },
        ],
      },
    ]) as any[];
    expect(traces).toHaveLength(1);
    expect(traces[0].base).toEqual([0, 6]);
    expect(traces[0].x).toEqual([6, 2]); // bar lengths = durations
    expect(traces[0].y).toEqual(["M1", "M1"]);
    expect(traces[0].text).toEqual(["A", "B"]);
  });

  it("colors tardy jobs in the danger color", () => {
    const [trace] = ganttTraces(
      [
        {
          label: "Jobs",
          jobs: [
            { id: "A", start: 0, end: 2 },
            { id: "C", start: 2, end: 10 },
          ],
        },
      ],
      new Set(["C"]),
    ) as any[];
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});
