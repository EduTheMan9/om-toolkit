import { describe, expect, it } from "vitest";
import { decodeDynamic, encodeDynamic } from "./urlState";

describe("dynamic lot-sizing URL state", () => {
  it("round-trips inputs through the query string", () => {
    const inputs = { demands: [50, 60, 90], setupCost: 150, holdingCost: 1 };
    expect(decodeDynamic("?" + encodeDynamic(inputs))).toEqual(inputs);
  });

  it("returns null for missing or garbage params", () => {
    expect(decodeDynamic("")).toBeNull();
    expect(decodeDynamic("?d=50,abc&s=150&h=1")).toBeNull();
  });
});
