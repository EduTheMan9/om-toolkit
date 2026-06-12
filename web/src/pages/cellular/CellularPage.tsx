import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { ApiError, postJson } from "../../lib/api";
import type { CellularResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { decodeCellular, encodeCellular } from "../../lib/urlState";
import { MetricCard } from "../../components/MetricCard";
import { PlotCard } from "../../components/PlotCard";
import "../../components/workbench.css";
import { MatrixEditor } from "./MatrixEditor";
import { RocDrawer } from "./RocDrawer";
import { clusteredTrace, incidenceTrace, names, partDisplayOrder, reorder } from "./charts";
import { CELLULAR_PRESETS } from "./presets";

const HEATMAP_LAYOUT = {
  xaxis: { side: "top" as const, showgrid: false },
  yaxis: { autorange: "reversed" as const, showgrid: false },
  margin: { l: 60, r: 16, t: 30, b: 10 },
};

export default function CellularPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [matrix, setMatrix] = useState<number[][]>(
    () =>
      decodeCellular("?" + searchParams.toString()) ??
      CELLULAR_PRESETS["Two clean cells (4×5)"],
  );
  const [result, setResult] = useState<CellularResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(matrix);

  const update = (next: number[][]) => {
    setMatrix(next);
    setSearchParams(encodeCellular(next), { replace: true });
  };

  useEffect(() => {
    let cancelled = false;
    postJson<CellularResponse>("/cellular/solve", { matrix: debounced })
      .then((res) => {
        if (!cancelled) {
          setResult(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Request failed");
      });
    return () => {
      cancelled = true;
    };
  }, [debounced]);

  // Everything below renders from the echoed result.matrix, never the live
  // input — the orders must index into the matrix they were computed from.
  const displayCols = result ? partDisplayOrder(result.col_order, result.part_cells) : [];
  const machineNames = result ? names("M", result.matrix.length) : [];
  const partNames = result ? names("P", result.matrix[0].length) : [];
  const cells = result
    ? Array.from({ length: result.n_cells }, (_, c) => ({
        machines: result.row_order
          .filter((i) => result.machine_cells[i] === c)
          .map((i) => machineNames[i])
          .join(", "),
        parts: result.col_order
          .filter((j) => result.part_cells[j] === c)
          .map((j) => partNames[j])
          .join(", "),
      }))
    : [];

  return (
    <div className="workbench">
      <div className="input-panel">
        <div>
          <h1>Cellular Manufacturing</h1>
          <div className="subtitle module-sub">
            Group machines into cells so each part family stays in one cell.
          </div>
        </div>
        <MatrixEditor matrix={matrix} onChange={update} />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = CELLULAR_PRESETS[e.target.value];
              if (preset) update(preset.map((row) => [...row]));
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(CELLULAR_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {result && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                Cells — machines that work as a team
              </div>
              <div className="hero-value">
                {result.n_cells} cells{" "}
                <span className="hero-detail">
                  grouping efficacy {formatNumber(result.grouping_efficacy)} ·
                  converged in {result.iterations} ROC pass
                  {result.iterations > 1 ? "es" : ""}
                </span>
              </div>
            </div>
            <div className="hero-orders">μ = (e − exceptional) / (e + voids)</div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="Grouping efficacy"
              value={formatNumber(result.grouping_efficacy)}
              detail="μ = 1 is a perfect block diagonal"
            />
            <MetricCard
              label="Exceptional elements"
              value={result.exceptional}
              detail="1s outside every cell — intercell travel"
            />
            <MetricCard
              label="Voids"
              value={result.voids}
              detail="0s inside a cell — idle pairings"
            />
          </div>
        )}
        {result && (
          <div className="row">
            <div style={{ flex: 1, minWidth: 0 }}>
              <PlotCard
                label="Original matrix"
                data={[incidenceTrace(result.matrix, machineNames, partNames)]}
                layout={HEATMAP_LAYOUT}
                height={110 + 36 * result.matrix.length}
              />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <PlotCard
                label="After ROC, grouped into cells — red = exceptional, gray = void"
                data={[
                  clusteredTrace(
                    reorder(result.matrix, result.row_order, displayCols),
                    result.row_order.map((i) => machineNames[i]),
                    displayCols.map((j) => partNames[j]),
                    result.row_order.map((i) => result.machine_cells[i]),
                    displayCols.map((j) => result.part_cells[j]),
                  ),
                ]}
                layout={HEATMAP_LAYOUT}
                height={110 + 36 * result.matrix.length}
              />
            </div>
          </div>
        )}
        {result && (
          <div className="row">
            {cells.map((cell, c) => (
              <MetricCard
                key={c}
                label={`Cell ${c + 1}`}
                value={cell.machines}
                detail={`parts: ${cell.parts}`}
              />
            ))}
          </div>
        )}
        {result && <RocDrawer steps={result.steps} />}
      </div>
    </div>
  );
}
