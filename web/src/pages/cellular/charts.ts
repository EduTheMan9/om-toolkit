import type { Data } from "plotly.js";

// Entry categories (indices into the discrete colorscale below).
const EMPTY = "#ffffff";
const VOID = "#d9d9d9"; // a 0 inside a cell: idle machine-part pairing
const IN_CELL = "#0d9488"; // a 1 inside its cell
const EXCEPTIONAL = "#dc2626"; // a 1 outside every cell: intercell travel
const SCALE: [number, string][] = [
  [0.0, EMPTY], [0.249, EMPTY],
  [0.25, VOID], [0.499, VOID],
  [0.5, IN_CELL], [0.749, IN_CELL],
  [0.75, EXCEPTIONAL], [1.0, EXCEPTIONAL],
];

export const names = (prefix: string, count: number) =>
  Array.from({ length: count }, (_, i) => `${prefix}${i + 1}`);

export function reorder(
  matrix: number[][],
  rowOrder: number[],
  colOrder: number[],
): number[][] {
  return rowOrder.map((i) => colOrder.map((j) => matrix[i][j]));
}

/** Part columns regrouped so each cell shows as one contiguous block:
 * stable sort of the ROC column order by each part's cell. */
export function partDisplayOrder(colOrder: number[], partCells: number[]): number[] {
  return [...colOrder].sort((a, b) => partCells[a] - partCells[b]);
}

/** Plain binary incidence matrix: teal = part visits machine. */
export function incidenceTrace(
  matrix: number[][],
  machineNames: string[],
  partNames: string[],
): Data {
  return {
    type: "heatmap",
    z: matrix,
    x: partNames,
    y: machineNames,
    zmin: 0,
    zmax: 1,
    colorscale: [[0, EMPTY], [0.499, EMPTY], [0.5, IN_CELL], [1, IN_CELL]],
    showscale: false,
    xgap: 2,
    ygap: 2,
    hovertemplate: "%{y} × %{x}: %{z}<extra></extra>",
  };
}

/** Clustered matrix colored by what each entry does to grouping efficacy.
 * All inputs must already be in display order. */
export function clusteredTrace(
  matrix: number[][],
  machineNames: string[],
  partNames: string[],
  machineCells: number[],
  partCells: number[],
): Data {
  const labels = ["", "void", "in cell", "exceptional"];
  const z = matrix.map((row, i) =>
    row.map((entry, j) => {
      const sameCell = machineCells[i] === partCells[j];
      if (entry === 1) return sameCell ? 2 : 3;
      return sameCell ? 1 : 0;
    }),
  );
  return {
    type: "heatmap",
    z,
    x: partNames,
    y: machineNames,
    zmin: 0,
    zmax: 3,
    colorscale: SCALE,
    showscale: false,
    xgap: 2,
    ygap: 2,
    customdata: z.map((row) => row.map((c) => labels[c])),
    hovertemplate: "%{y} × %{x}: %{customdata}<extra></extra>",
  } as Data;
}
