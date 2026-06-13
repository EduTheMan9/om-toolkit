import { describe, expect, it } from "vitest";
import {
  capacityTrace,
  operatingPointTrace,
  perHour,
  utilizationTrace,
  vutBreakdownTrace,
  waitCurveTrace,
} from "./charts";

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

describe("waitCurveTrace", () => {
  it("plots Wq against utilization as a line", () => {
    const trace = waitCurveTrace({ rho: [0.5, 0.9], wq: [0.1, 0.9], lq: [0.05, 0.81] }) as any;
    expect(trace.type).toBe("scatter");
    expect(trace.mode).toBe("lines");
    expect(trace.x).toEqual([0.5, 0.9]);
    expect(trace.y).toEqual([0.1, 0.9]);
  });
});

describe("operatingPointTrace", () => {
  it("marks the user's operating point", () => {
    const trace = operatingPointTrace(0.8, 0.4) as any;
    expect(trace.mode).toBe("markers");
    expect(trace.x).toEqual([0.8]);
    expect(trace.y).toEqual([0.4]);
  });
});

describe("vutBreakdownTrace", () => {
  it("shows the three factors as bars", () => {
    const trace = vutBreakdownTrace(1, 4, 0.1) as any;
    expect(trace.type).toBe("bar");
    expect(trace.y).toEqual([1, 4, 0.1]);
    expect(trace.x.length).toBe(3);
  });
});
