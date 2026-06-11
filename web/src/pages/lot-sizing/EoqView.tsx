import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { EoqResponse } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";

export interface EoqInputs {
  demand: number;
  orderingCost: number;
  holdingCost: number;
}

export const EOQ_DEFAULTS: EoqInputs = { demand: 1200, orderingCost: 100, holdingCost: 6 };

export function EoqView({
  inputs,
  onInputs,
}: {
  inputs: EoqInputs;
  onInputs: (next: EoqInputs) => void;
}) {
  const [result, setResult] = useState<EoqResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<EoqResponse>("/lot-sizing/eoq", {
      demand: debounced.demand,
      ordering_cost: debounced.orderingCost,
      holding_cost: debounced.holdingCost,
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
          <h1>Lot Sizing</h1>
          <div className="subtitle module-sub">
            Constant demand: the classic ordering-vs-holding trade-off.
          </div>
        </div>
        <NumberField
          label="Demand D (units/period)"
          value={inputs.demand}
          onChange={(demand) => onInputs({ ...inputs, demand })}
        />
        <NumberField
          label="Ordering cost S"
          value={inputs.orderingCost}
          onChange={(orderingCost) => onInputs({ ...inputs, orderingCost })}
        />
        <NumberField
          label="Holding cost H"
          value={inputs.holdingCost}
          onChange={(holdingCost) => onInputs({ ...inputs, holdingCost })}
        />
        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  Optimal order quantity
                </div>
                <div className="hero-value">
                  Q* = {result.quantity.toFixed(1)}{" "}
                  <span className="hero-detail">
                    units · {formatMoney(result.total_cost)} total ·{" "}
                    {result.orders_per_period.toFixed(2)} orders/period
                  </span>
                </div>
              </div>
            </div>
            <div className="row">
              <MetricCard label="Ordering cost" value={formatMoney(result.ordering_cost_total)} />
              <MetricCard label="Holding cost" value={formatMoney(result.holding_cost_total)} />
              <MetricCard
                label="Time between orders"
                value={result.time_between_orders.toFixed(3)}
                detail="periods"
              />
            </div>
            <PlotCard
              label="The trade-off: ordering falls, holding rises — Q* is the crossing"
              data={[
                { type: "scatter", x: result.curve.q, y: result.curve.ordering, name: "Ordering (D/Q)·S", line: { color: "#94a3b8" } },
                { type: "scatter", x: result.curve.q, y: result.curve.holding, name: "Holding (Q/2)·H", line: { color: "#cbd5e1" } },
                { type: "scatter", x: result.curve.q, y: result.curve.total, name: "Total", line: { color: "#0d9488", width: 3 } },
              ]}
              layout={{
                xaxis: { title: { text: "order quantity Q" } },
                yaxis: { range: [0, result.total_cost * 3] },
              }}
              height={320}
            />
          </>
        )}
      </div>
    </>
  );
}
