import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { LittlesLawResponse, LittlesVariable } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";

const INFO: Record<LittlesVariable, { label: string; unit: string }> = {
  inventory: { label: "Inventory I", unit: "units in the process" },
  flow_rate: { label: "Flow rate R", unit: "units per time" },
  flow_time: { label: "Flow time T", unit: "time in the process" },
};
const FORMULA: Record<LittlesVariable, string> = {
  inventory: "I = R × T",
  flow_rate: "R = I ÷ T",
  flow_time: "T = I ÷ R",
};
const ORDER: LittlesVariable[] = ["inventory", "flow_rate", "flow_time"];

export interface LittlesInputs {
  solveFor: LittlesVariable;
  inventory: number;
  flowRate: number;
  flowTime: number;
}

export const LITTLES_DEFAULTS: LittlesInputs = {
  solveFor: "flow_time",
  inventory: 20,
  flowRate: 4,
  flowTime: 5,
};

export function LittlesView({
  inputs,
  onInputs,
}: {
  inputs: LittlesInputs;
  onInputs: (next: LittlesInputs) => void;
}) {
  const [result, setResult] = useState<LittlesLawResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<LittlesLawResponse>("/process-analysis/littles-law", {
      inventory: debounced.solveFor === "inventory" ? null : debounced.inventory,
      flow_rate: debounced.solveFor === "flow_rate" ? null : debounced.flowRate,
      flow_time: debounced.solveFor === "flow_time" ? null : debounced.flowTime,
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

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Little's Law</h1>
          <div className="subtitle module-sub">
            I = R × T — know two, get the third. Holds for any stable process.
          </div>
        </div>
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Solve for</div>
          <div className="mode-pills">
            {ORDER.map((v) => (
              <button
                key={v}
                className={inputs.solveFor === v ? "active" : ""}
                onClick={() => onInputs({ ...inputs, solveFor: v })}
              >
                {v === "inventory" ? "I" : v === "flow_rate" ? "R" : "T"}
              </button>
            ))}
          </div>
        </div>
        {inputs.solveFor !== "inventory" && (
          <NumberField
            label="Inventory I (units)"
            value={inputs.inventory}
            onChange={(inventory) => onInputs({ ...inputs, inventory })}
          />
        )}
        {inputs.solveFor !== "flow_rate" && (
          <NumberField
            label="Flow rate R (units/time)"
            value={inputs.flowRate}
            onChange={(flowRate) => onInputs({ ...inputs, flowRate })}
          />
        )}
        {inputs.solveFor !== "flow_time" && (
          <NumberField
            label="Flow time T (time)"
            value={inputs.flowTime}
            onChange={(flowTime) => onInputs({ ...inputs, flowTime })}
          />
        )}
        <div className="subtitle" style={{ fontSize: 11 }}>
          Use consistent units — e.g. R in units/min and T in minutes.
        </div>
        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  {FORMULA[result.solved_for]}
                </div>
                <div className="hero-value">
                  {INFO[result.solved_for].label} ={" "}
                  {formatNumber(result[result.solved_for])}{" "}
                  <span className="hero-detail">{INFO[result.solved_for].unit}</span>
                </div>
              </div>
            </div>
            <div className="row">
              {ORDER.map((v) => (
                <MetricCard
                  key={v}
                  label={INFO[v].label}
                  value={formatNumber(result[v])}
                  detail={v === result.solved_for ? "solved" : "given"}
                  selected={v === result.solved_for}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </>
  );
}
