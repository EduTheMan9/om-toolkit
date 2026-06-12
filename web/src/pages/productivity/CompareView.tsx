import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { ProductivityResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { ProductivityInputs } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { MultifactorDrawer } from "./MultifactorDrawer";
import { changeTrace, formatChange } from "./charts";
import { PRODUCTIVITY_PRESETS } from "./presets";

export function CompareView({
  inputs,
  onInputs,
}: {
  inputs: ProductivityInputs;
  onInputs: (next: ProductivityInputs) => void;
}) {
  const [result, setResult] = useState<ProductivityResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<ProductivityResponse>("/productivity/compare", {
      previous_output: debounced.outputPrevious,
      current_output: debounced.outputCurrent,
      inputs: debounced.inputs,
    })
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

  // Chart rows: defined factors plus the all-inputs multifactor row.
  const chartNames = result
    ? [...result.factors.filter((f) => f.change !== null).map((f) => f.name), "Multifactor (all inputs)"]
    : [];
  const chartChanges = result
    ? [...result.factors.filter((f) => f.change !== null).map((f) => f.change!), result.multifactor.change]
    : [];

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Productivity</h1>
          <div className="subtitle module-sub">
            Did we actually get more productive? Compare two periods, honestly.
          </div>
        </div>
        <JobsTable
          label="Input costs ($, both periods)"
          idLabel="input"
          columns={["last $", "this $"]}
          rows={inputs.inputs.map((r) => ({ id: r.name, a: r.previous, b: r.current }))}
          onChange={(rows) =>
            onInputs({
              ...inputs,
              inputs: rows.map((row) => ({ name: row.id, previous: row.a, current: row.b })),
            })
          }
        />
        <NumberField
          label="Output value, last period ($)"
          value={inputs.outputPrevious}
          onChange={(outputPrevious) => onInputs({ ...inputs, outputPrevious })}
        />
        <NumberField
          label="Output value, this period ($)"
          value={inputs.outputCurrent}
          onChange={(outputCurrent) => onInputs({ ...inputs, outputCurrent })}
        />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = PRODUCTIVITY_PRESETS[e.target.value];
              if (preset) onInputs({ ...preset, inputs: preset.inputs.map((r) => ({ ...r })) });
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(PRODUCTIVITY_PRESETS).map((name) => (
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
                Multifactor productivity change — the honest aggregate
              </div>
              <div className="hero-value">
                {formatChange(result.multifactor.change)}{" "}
                <span className="hero-detail">
                  {formatNumber(result.multifactor.previous)} →{" "}
                  {formatNumber(result.multifactor.current)} $ out per $ in
                </span>
              </div>
            </div>
            <div className="hero-orders">P = output value ÷ Σ input costs</div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="Multifactor, last period"
              value={formatNumber(result.multifactor.previous)}
              detail="$ output per $ of ALL inputs"
            />
            <MetricCard
              label="Multifactor, this period"
              value={formatNumber(result.multifactor.current)}
              detail="$ output per $ of ALL inputs"
            />
            <MetricCard
              label="Change"
              value={formatChange(result.multifactor.change)}
              detail="ratio change, not a difference"
            />
          </div>
        )}
        {result && (
          <div className="card" style={{ padding: "12px 14px" }}>
            <div className="label">Productivity by factor ($ output per $ of that input)</div>
            <table style={{ width: "100%", fontSize: 12, borderSpacing: 0, marginTop: 6 }}>
              <thead>
                <tr style={{ textAlign: "left", color: "var(--subtle)" }}>
                  <th style={{ paddingBottom: 4 }}>factor</th>
                  <th>last</th>
                  <th>this</th>
                  <th>change</th>
                </tr>
              </thead>
              <tbody>
                {[...result.factors, { name: "Multifactor (all inputs)", ...result.multifactor }].map(
                  (f) => (
                    <tr key={f.name}>
                      <td style={{ padding: "3px 0" }}>{f.name}</td>
                      <td>{f.previous === null ? "—" : formatNumber(f.previous)}</td>
                      <td>{f.current === null ? "—" : formatNumber(f.current)}</td>
                      <td>{f.change === null ? "—" : formatChange(f.change)}</td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
            <div className="subtitle" style={{ fontSize: 11, marginTop: 6 }}>
              A single factor can look great while the others absorb the load —
              the multifactor row is the one that says whether the operation as
              a whole got more productive.
            </div>
          </div>
        )}
        {result && (
          <PlotCard
            label="Productivity change by factor — left of the line means less productive"
            data={[changeTrace(chartNames, chartChanges)]}
            layout={{
              xaxis: { title: { text: "change (%)" } },
              yaxis: { autorange: "reversed" },
              shapes: [
                {
                  type: "line",
                  yref: "paper",
                  x0: 0,
                  x1: 0,
                  y0: 0,
                  y1: 1,
                  line: { color: "#101418", width: 1 },
                },
              ],
            }}
            height={110 + 36 * chartNames.length}
          />
        )}
        {result && <MultifactorDrawer steps={result.steps} />}
      </div>
    </>
  );
}
