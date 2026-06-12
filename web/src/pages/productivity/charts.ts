import type { Data } from "plotly.js";

/** +0.108 -> "+10.8%" — productivity change is a fraction in core/API. */
export const formatChange = (change: number) =>
  `${change >= 0 ? "+" : ""}${(change * 100).toFixed(1)}%`;

/** Change per factor: bars left of the zero line mean the factor got LESS
 * productive. The zero line is a layout shape added by the view. */
export function changeTrace(names: string[], changes: number[]): Data {
  return {
    type: "bar",
    orientation: "h",
    y: names,
    x: changes.map((c) => c * 100),
    marker: { color: changes.map((c) => (c < 0 ? "#dc2626" : "#0d9488")) },
    text: changes.map(formatChange),
    textposition: "outside",
    hoverinfo: "skip",
    showlegend: false,
  };
}
