import type { Data } from "plotly.js";
import type { ScheduledJob } from "./api";

const ON_TIME = "#0d9488";
const TARDY = "#dc2626";

/** One horizontal bar trace per machine row, positioned with `base` so bars
 * start at each job's start time. Pair with layout barmode "overlay" and a
 * reversed y-axis (so the first row renders on top). */
export function ganttTraces(
  rows: { label: string; jobs: ScheduledJob[] }[],
  tardy: Set<string> = new Set(),
): Data[] {
  return rows.map((row) => ({
    type: "bar" as const,
    orientation: "h" as const,
    y: row.jobs.map(() => row.label),
    base: row.jobs.map((j) => j.start),
    x: row.jobs.map((j) => j.end - j.start),
    text: row.jobs.map((j) => j.id),
    textposition: "inside" as const,
    insidetextanchor: "middle" as const,
    hovertemplate: "%{text}<extra></extra>",
    marker: {
      color: row.jobs.map((j) => (tardy.has(j.id) ? TARDY : ON_TIME)),
      line: { color: "#ffffff", width: 1 },
    },
    showlegend: false,
  }));
}
