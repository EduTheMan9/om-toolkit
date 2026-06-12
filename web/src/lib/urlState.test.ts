import { describe, expect, it } from "vitest";
import {
  decodeBalancing,
  decodeCellular,
  decodeDispatch,
  decodeDynamic,
  decodeJohnson,
  decodeProcess,
  decodeProductivity,
  encodeBalancing,
  encodeCellular,
  encodeDispatch,
  encodeDynamic,
  encodeJohnson,
  encodeProcess,
  encodeProductivity,
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

describe("process analysis URL state", () => {
  it("round-trips resources and a known demand", () => {
    const inputs = {
      resources: [
        { name: "Take order", timeMin: 1.5, servers: 1 },
        { name: "Make sandwich", timeMin: 3, servers: 2 },
      ],
      demandPerHour: 35,
    };
    expect(decodeProcess("?" + encodeProcess(inputs))).toEqual(inputs);
  });

  it("round-trips capacity-only inputs (no demand)", () => {
    const inputs = {
      resources: [{ name: "A", timeMin: 10, servers: 2 }],
      demandPerHour: null,
    };
    expect(decodeProcess("?" + encodeProcess(inputs))).toEqual(inputs);
  });

  it("returns null for malformed resource strings", () => {
    expect(decodeProcess("")).toBeNull();
    expect(decodeProcess("?r=A,x,1")).toBeNull();
    expect(decodeProcess("?r=A,10,2&d=abc")).toBeNull();
  });
});

describe("productivity URL state", () => {
  it("round-trips outputs and input costs", () => {
    const inputs = {
      outputPrevious: 5000,
      outputCurrent: 6000,
      inputs: [
        { name: "Labor", previous: 1500, current: 1600 },
        { name: "Overhead", previous: 500, current: 500 },
      ],
    };
    expect(decodeProductivity("?" + encodeProductivity(inputs))).toEqual(inputs);
  });

  it("returns null for malformed strings", () => {
    expect(decodeProductivity("")).toBeNull();
    expect(decodeProductivity("?i=Labor,x,1&o=5,6")).toBeNull();
    expect(decodeProductivity("?i=Labor,1,2&o=5")).toBeNull();
  });
});

describe("cellular URL state", () => {
  it("round-trips the worked example matrix", () => {
    const matrix = [
      [1, 0, 0, 1, 0],
      [0, 1, 1, 0, 1],
      [1, 0, 0, 1, 0],
      [0, 1, 1, 0, 0],
    ];
    expect(decodeCellular("?" + encodeCellular(matrix))).toEqual(matrix);
  });

  it("returns null for malformed or ragged matrices", () => {
    expect(decodeCellular("")).toBeNull();
    expect(decodeCellular("?m=10a10")).toBeNull();
    expect(decodeCellular("?m=10;1")).toBeNull();
  });
});
