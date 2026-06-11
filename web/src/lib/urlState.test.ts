import { describe, expect, it } from "vitest";
import {
  decodeBalancing,
  decodeDispatch,
  decodeDynamic,
  decodeJohnson,
  encodeBalancing,
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

describe("line balancing URL state", () => {
  it("round-trips tasks with predecessors and a direct cycle time", () => {
    const inputs = {
      tasks: [
        { id: "A", duration: 5, predecessors: [] },
        { id: "F", duration: 4, predecessors: ["D", "E"] },
      ],
      cycleTime: 10,
      availableTime: null,
      demand: null,
    };
    expect(decodeBalancing("?" + encodeBalancing(inputs))).toEqual(inputs);
  });

  it("round-trips demand-mode inputs", () => {
    const inputs = {
      tasks: [{ id: "A", duration: 5, predecessors: [] }],
      cycleTime: null,
      availableTime: 480,
      demand: 70,
    };
    expect(decodeBalancing("?" + encodeBalancing(inputs))).toEqual(inputs);
  });

  it("returns null for malformed task strings or missing cycle info", () => {
    expect(decodeBalancing("")).toBeNull();
    expect(decodeBalancing("?t=A,5,&ct=abc")).toBeNull();
    expect(decodeBalancing("?t=A,x,&ct=10")).toBeNull();
    expect(decodeBalancing("?t=A,5,")).toBeNull(); // no ct and no at+dm
  });
});
