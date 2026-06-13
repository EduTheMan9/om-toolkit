import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { OeeResponse } from "../../lib/api";
import { formatNumber, formatPercent } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { OeeDrawer } from "./OeeDrawer";

export interface OeeInputs {
  plannedTime: number;
  downtime: number;
  idealCycleTime: number;
  totalCount: number;
  goodCount: number;
}

// The "classic shift" worked example from tests/test_oee.py (OEE = 17/21).
const DEFAULT: OeeInputs = {
  plannedTime: 420,
  downtime: 30,
  idealCycleTime: 1,
  totalCount: 360,
  goodCount: 340,
};

/** Overall Equipment Effectiveness: Availability × Performance × Quality.
 * The most recognized equipment KPI — each factor is an independent loss
 * stacked on the same planned time. */
export function OeeView() {
  const [inputs, setInputs] = useState<OeeInputs>(DEFAULT);
  const [result, setResult] = useState<OeeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<OeeResponse>("/productivity/oee", {
      planned_time: debounced.plannedTime,
      downtime: debounced.downtime,
      ideal_cycle_time: debounced.idealCycleTime,
      total_count: debounced.totalCount,
      good_count: debounced.goodCount,
    })
      .then((res) => {
        if (!cancelled) {
          setResult(res);
          setError(null);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setResult(null);
          setError(err instanceof ApiError ? err.message : "Request failed");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [debounced]);

  const set = (patch: Partial<OeeInputs>) => setInputs((prev) => ({ ...prev, ...patch }));

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>OEE</h1>
          <div className="subtitle module-sub">
            Overall Equipment Effectiveness — how much of the planned time
            actually turned into good product, split into three honest losses.
          </div>
        </div>
        <NumberField label="Planned production time (min)" value={inputs.plannedTime} onChange={(v) => set({ plannedTime: v })} />
        <NumberField label="Downtime / stops (min)" value={inputs.downtime} onChange={(v) => set({ downtime: v })} />
        <NumberField label="Ideal cycle time (min / unit)" value={inputs.idealCycleTime} onChange={(v) => set({ idealCycleTime: v })} />
        <NumberField label="Total units produced" value={inputs.totalCount} onChange={(v) => set({ totalCount: v })} />
        <NumberField label="Good units (passed quality)" value={inputs.goodCount} onChange={(v) => set({ goodCount: v })} />
        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  OEE — Availability × Performance × Quality
                </div>
                <div className="hero-value">
                  {formatPercent(result.oee)}{" "}
                  <span className="hero-detail">of the planned time became good product</span>
                </div>
              </div>
              <div className="hero-orders">A × P × Q</div>
            </div>
            <div className="row">
              <MetricCard
                label="Availability"
                value={formatPercent(result.availability)}
                detail={`ran ${formatNumber(result.run_time)} of ${formatNumber(inputs.plannedTime)} planned min — stop losses`}
              />
              <MetricCard
                label="Performance"
                value={formatPercent(result.performance)}
                detail="actual pace vs the ideal cycle time — speed losses"
              />
              <MetricCard
                label="Quality"
                value={formatPercent(result.quality)}
                detail="good units of total produced — defect losses"
              />
            </div>
            <OeeDrawer steps={result.steps} />
          </>
        )}
      </div>
    </>
  );
}
