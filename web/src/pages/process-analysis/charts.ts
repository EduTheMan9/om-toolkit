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
