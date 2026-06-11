import { describe, expect, it } from "vitest";
import {
  decodeDispatch,
  decodeDynamic,
  decodeJohnson,
  encodeDispatch,
  encodeDynamic,
  encodeJohnson,
} from "./urlState";

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

describe("scheduling URL state", () => {
  it("round-trips dispatch jobs through the query string", () => {
    const jobs = [
      { id: "A", processingTime: 6, dueDate: 8 },
      { id: "B", processingTime: 2, dueDate: 6 },
    ];
    expect(decodeDispatch("?" + encodeDispatch(jobs))).toEqual(jobs);
  });

  it("round-trips johnson jobs and ignores extra params like mode", () => {
    const jobs = [{ id: "J1", timeM1: 3, timeM2: 6 }];
    expect(decodeJohnson("?mode=johnson&" + encodeJohnson(jobs))).toEqual(jobs);
  });

  it("returns null for missing or malformed job strings", () => {
    expect(decodeDispatch("")).toBeNull();
    expect(decodeDispatch("?j=A,1")).toBeNull(); // wrong arity
    expect(decodeDispatch("?j=A,x,2")).toBeNull(); // non-numeric
  });
});
