import { describe, expect, it } from "vitest";
import { capacityTrace, perHour, utilizationTrace } from "./charts";

const RESOURCES = [
  { name: "A", processing_time: 10, servers: 2, capacity: 0.2, utilization: 0.75, implied_utilization: 0.75 },
  { name: "B", processing_time: 6, servers: 1, capacity: 1 / 6, utilization: 0.9, implied_utilization: 0.9 },
];

describe("capacityTrace", () => {
  it("converts per-minute capacities to units/hour and flags the bottleneck", () => {
    const trace = capacityTrace(RESOURCES, "B") as any;
    expect(trace.y[0]).toBeCloseTo(12); // 0.2/min * 60
    expect(trace.y[1]).toBeCloseTo(10);
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});

describe("utilizationTrace", () => {
  it("shows percentages and turns overload (>100%) red", () => {
    const trace = utilizationTrace(["A", "B"], [0.75, 1.2]) as any;
    expect(trace.x).toEqual([75, 120]);
    expect(trace.text).toEqual(["75%", "120%"]);
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});

describe("perHour", () => {
  it("formats a per-minute rate as units per hour", () => {
    expect(perHour(1 / 6)).toBe("10");
    expect(perHour(0.15)).toBe("9");
  });
});
