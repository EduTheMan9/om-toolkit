import type { Data } from "plotly.js";
import type { ProcessResource } from "../../lib/api";
import { formatNumber } from "../../lib/format";

/** Core and the API are unit-agnostic (per-minute); the UI convention is
 * processing times in minutes and rates in units/hour. */
export const perHour = (perMin: number) => formatNumber(perMin * 60);

/** Capacity per resource in units/hour; the bottleneck bar is red.
 * The dashed demand line is a layout shape added by the view. */
export function capacityTrace(
  resources: ProcessResource[],
  bottleneckName: string,
): Data {
  return {
    type: "bar",
    x: resources.map((r) => r.name),
    y: resources.map((r) => r.capacity * 60),
    marker: {
      color: resources.map((r) =>
        r.name === bottleneckName ? "#dc2626" : "#0d9488",
      ),
    },
    text: resources.map((r) => perHour(r.capacity)),
    textposition: "outside",
    hoverinfo: "x+y",
    showlegend: false,
  };
}

/** The signature queueing curve: mean wait Wq explodes as utilization -> 1. */
export function waitCurveTrace(curve: { rho: number[]; wq: number[]; lq?: number[] }): Data {
  return {
    type: "scatter",
    mode: "lines",
    x: curve.rho,
    y: curve.wq,
    line: { color: "#0d9488", width: 2 },
    hovertemplate: "ρ=%{x:.2f}<br>Wq=%{y:.3f}<extra></extra>",
    name: "Wq",
    showlegend: false,
  };
}

/** Red dot marking where the user's inputs sit on the wait curve. */
export function operatingPointTrace(rho: number, wq: number): Data {
  return {
    type: "scatter",
    mode: "markers",
    x: [rho],
    y: [wq],
    marker: { color: "#dc2626", size: 10 },
    hovertemplate: "operating point<br>ρ=%{x:.2f}<br>Wq=%{y:.3f}<extra></extra>",
    showlegend: false,
  };
}

/** V × U × T decomposition of the approximate wait, as three bars. */
export function vutBreakdownTrace(v: number, u: number, t: number): Data {
  return {
    type: "bar",
    x: ["V (variability)", "U (utilization)", "T (time)"],
    y: [v, u, t],
    marker: { color: "#0d9488" },
    text: [v, u, t].map((n) => formatNumber(n)),
    textposition: "outside",
    hoverinfo: "skip",
    showlegend: false,
  };
}

/** Horizontal utilization bars; anything past the 100% line is overload. */
export function utilizationTrace(names: string[], values: number[]): Data {
  return {
    type: "bar",
    orientation: "h",
    y: names,
    x: values.map((v) => v * 100),
    marker: {
      color: values.map((v) => (v > 1 ? "#dc2626" : "#0d9488")),
    },
    text: values.map((v) => `${Math.round(v * 100)}%`),
    textposition: "outside",
    hoverinfo: "skip",
    showlegend: false,
  };
}
