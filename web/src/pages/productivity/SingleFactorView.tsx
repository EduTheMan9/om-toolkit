import { useState } from "react";
import { formatNumber } from "../../lib/format";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";

/** Output per unit of ONE input, in whatever units you like. Pure display
 * math (output ÷ input), so it stays client-side per the module spec. */
export function SingleFactorView() {
  const [output, setOutput] = useState(500);
  const [inputAmount, setInputAmount] = useState(200);

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Single-factor productivity</h1>
          <div className="subtitle module-sub">
            Output per unit of ONE input — units per labor-hour, titles per
            clerk, € per kWh.
          </div>
        </div>
        <NumberField label="Output (units)" value={output} onChange={setOutput} />
        <NumberField
          label="Input (e.g. labor-hours)"
          value={inputAmount}
          onChange={setInputAmount}
        />
        {inputAmount <= 0 && <div className="error-text">Input amount must be positive.</div>}
      </div>

      <div className="results-pane">
        {inputAmount > 0 && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  Single-factor productivity
                </div>
                <div className="hero-value">
                  {formatNumber(output / inputAmount)}{" "}
                  <span className="hero-detail">output per unit of input</span>
                </div>
              </div>
              <div className="hero-orders">P = output ÷ input</div>
            </div>
            <div className="row">
              <MetricCard
                label="Why a ratio?"
                value={formatNumber(output / inputAmount)}
                detail="ratios compare across plants, periods, and company sizes — raw output never does"
              />
            </div>
          </>
        )}
      </div>
    </>
  );
}
