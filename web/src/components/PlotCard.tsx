import { lazy, Suspense } from "react";
import type { Data, Layout } from "plotly.js";

// Plotly is ~4 MB minified — by far the heaviest dependency. Loading it lazily
// keeps it out of the entry bundle so the app shell (and pages without charts)
// load fast; the chunk is fetched only when a chart first mounts. Only `type`
// imports remain static here, and those are erased at build time.
const PlotFigure = lazy(() => import("./PlotFigure"));

export function PlotCard({
  label,
  data,
  layout,
  height = 280,
}: {
  label: string;
  data: Data[];
  layout?: Partial<Layout>;
  height?: number;
}) {
  return (
    <div className="card" style={{ padding: "12px 14px" }}>
      <div className="label">{label}</div>
      {/* Reserve the chart's height while the Plotly chunk loads to avoid layout shift. */}
      <Suspense fallback={<div style={{ height }} />}>
        <PlotFigure data={data} layout={layout} height={height} />
      </Suspense>
    </div>
  );
}
