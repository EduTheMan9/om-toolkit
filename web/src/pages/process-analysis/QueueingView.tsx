import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { QueueingResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { operatingPointTrace, vutBreakdownTrace, waitCurveTrace } from "./charts";

export interface QueueingInputs {
  lam: number;
  mu: number;
  c: number;
  ca: number;
  cs: number;
}

export const QUEUEING_DEFAULTS: QueueingInputs = {
  lam: 8,
  mu: 10,
  c: 1,
  ca: 1,
  cs: 1,
};

export const QUEUEING_PRESETS: Record<string, QueueingInputs> = {
  "Single server (M/M/1)": { lam: 8, mu: 10, c: 1, ca: 1, cs: 1 },
  "Two servers (M/M/2)": { lam: 2, mu: 1.5, c: 2, ca: 1, cs: 1 },
  "Steady arrivals (low variability)": { lam: 8, mu: 10, c: 1, ca: 0.25, cs: 1 },
};

export function QueueingView({
  inputs,
  onInputs,
}: {
  inputs: QueueingInputs;
  onInputs: (next: QueueingInputs) => void;
}) {
  const [result, setResult] = useState<QueueingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<QueueingResponse>("/process-analysis/queueing", debounced)
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

  const exactLabel = result?.exact.is_exact_for_inputs
    ? `exact ${result.exact.model}`
    : `${result?.exact.model} reference (Ca=Cs=1)`;

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Queueing (VUT)</h1>
          <div className="subtitle module-sub">
            Wq ≈ V × U × T — variability, utilization, and service time set the wait.
          </div>
        </div>
        <NumberField
          label="Arrival rate λ (per time)"
          value={inputs.lam}
          onChange={(lam) => onInputs({ ...inputs, lam })}
        />
        <NumberField
          label="Service rate μ (per server, per time)"
          value={inputs.mu}
          onChange={(mu) => onInputs({ ...inputs, mu })}
        />
        <NumberField
          label="Servers c"
          value={inputs.c}
          onChange={(c) => onInputs({ ...inputs, c })}
        />
        <NumberField
          label="Arrival CV (Ca)"
          value={inputs.ca}
          onChange={(ca) => onInputs({ ...inputs, ca })}
        />
        <NumberField
          label="Service CV (Cs)"
          value={inputs.cs}
          onChange={(cs) => onInputs({ ...inputs, cs })}
        />
        <div className="subtitle" style={{ fontSize: 11 }}>
          CV = 1 is Markovian (exact). CV &lt; 1 is steadier, &gt; 1 is burstier.
        </div>
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = QUEUEING_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(QUEUEING_PRESETS).map((name) => (
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
                Utilization ρ = λ / (c × μ)
              </div>
              <div className="hero-value">
                {Math.round(result.vut.rho * 100)}%{" "}
                <span className="hero-detail">
                  approx wait Wq {formatNumber(result.vut.Wq)} · in system W{" "}
                  {formatNumber(result.vut.W)}
                </span>
              </div>
            </div>
            <div className="hero-orders">Wq = V × U × T</div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="In queue Lq"
              value={formatNumber(result.vut.Lq)}
              detail={`exact ${formatNumber(result.exact.Lq)}`}
            />
            <MetricCard
              label="In system L"
              value={formatNumber(result.vut.L)}
              detail={`exact ${formatNumber(result.exact.L)}`}
            />
            <MetricCard
              label="Wait Wq"
              value={formatNumber(result.vut.Wq)}
              detail={`${exactLabel}: ${formatNumber(result.exact.Wq)}`}
            />
            <MetricCard
              label="In system W"
              value={formatNumber(result.vut.W)}
              detail={`exact ${formatNumber(result.exact.W)}`}
            />
          </div>
        )}
        {result && (
          <PlotCard
            label="Wait vs utilization — the wait explodes as ρ → 1"
            data={[
              waitCurveTrace(result.curve),
              operatingPointTrace(result.vut.rho, result.vut.Wq),
            ]}
            layout={{
              xaxis: { title: { text: "utilization ρ" }, range: [0, 1] },
              yaxis: { title: { text: "Wq (wait)" } },
            }}
            height={260}
          />
        )}
        {result && (
          <PlotCard
            label="VUT breakdown — the three factors multiply to Wq"
            data={[vutBreakdownTrace(result.vut.V, result.vut.U, result.vut.T)]}
            layout={{ yaxis: { title: { text: "factor value" } } }}
            height={220}
          />
        )}
      </div>
    </>
  );
}
