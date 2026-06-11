import Plotly from "plotly.js-dist-min";
import createPlotlyComponent from "react-plotly.js/factory";
import type { Data, Layout } from "plotly.js";

const Plot = createPlotlyComponent(Plotly);

const BASE_LAYOUT: Partial<Layout> = {
  font: { family: "Inter, sans-serif", size: 12, color: "#101418" },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  margin: { l: 40, r: 16, t: 16, b: 32 },
};

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
      <Plot
        data={data}
        layout={{ ...BASE_LAYOUT, ...layout, height }}
        config={{ displayModeBar: false, responsive: true }}
        style={{ width: "100%" }}
        useResizeHandler
      />
    </div>
  );
}
