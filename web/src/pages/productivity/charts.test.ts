import { describe, expect, it } from "vitest";
import { changeTrace, formatChange } from "./charts";

describe("changeTrace", () => {
  it("shows percent changes with negatives in red", () => {
    const trace = changeTrace(["Labor", "Machines"], [0.125, -0.046]) as any;
    expect(trace.x[0]).toBeCloseTo(12.5);
    expect(trace.text).toEqual(["+12.5%", "-4.6%"]);
    expect(trace.marker.color).toEqual(["#0d9488", "#dc2626"]);
  });
});

describe("formatChange", () => {
  it("formats a fraction as a signed percentage", () => {
    expect(formatChange(7 / 65)).toBe("+10.8%");
    expect(formatChange(-0.2)).toBe("-20.0%");
  });
});
