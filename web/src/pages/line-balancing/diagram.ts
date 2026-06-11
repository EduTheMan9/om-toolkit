import type { Data } from "plotly.js";
import type { BalancingTask } from "../../lib/urlState";

/** Lay the precedence diagram out on the Kilbridge grid: x = column
 * (precedence depth), y spreads the tasks within a column around 0.
 * Returns [edge trace, node trace] for a Plotly scatter. */
export function precedenceTraces(
  tasks: BalancingTask[],
  columns: Record<string, number>,
): Data[] {
  const byColumn = new Map<number, string[]>();
  for (const t of tasks) {
    const col = columns[t.id];
    if (!byColumn.has(col)) byColumn.set(col, []);
    byColumn.get(col)!.push(t.id);
  }
  const pos = new Map<string, { x: number; y: number }>();
  for (const [col, ids] of byColumn) {
    ids.forEach((id, i) => pos.set(id, { x: col, y: i - (ids.length - 1) / 2 }));
  }

  const edgeX: (number | null)[] = [];
  const edgeY: (number | null)[] = [];
  for (const t of tasks) {
    for (const p of t.predecessors) {
      const from = pos.get(p);
      const to = pos.get(t.id);
      if (!from || !to) continue;
      edgeX.push(from.x, to.x, null); // null breaks the line between edges
      edgeY.push(from.y, to.y, null);
    }
  }

  const durations = new Map(tasks.map((t) => [t.id, t.duration]));
  const ids = tasks.map((t) => t.id);
  return [
    {
      type: "scatter",
      mode: "lines",
      x: edgeX,
      y: edgeY,
      line: { color: "#cbd5e1", width: 1.5 },
      hoverinfo: "skip",
      showlegend: false,
    },
    {
      type: "scatter",
      mode: "markers+text",
      x: ids.map((id) => pos.get(id)!.x),
      y: ids.map((id) => pos.get(id)!.y),
      text: ids,
      textposition: "middle center",
      textfont: { color: "#ffffff", size: 11, family: "Inter, sans-serif" },
      marker: { size: 30, color: "#0d9488" },
      hovertext: ids.map((id) => `${id}: ${durations.get(id)} time units`),
      hoverinfo: "text",
      showlegend: false,
    },
  ];
}
