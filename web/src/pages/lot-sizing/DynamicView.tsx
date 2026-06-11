import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { DynamicResponse, PlanName } from "../../lib/api";
import { formatMoney, percentGap } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { DynamicInputs } from "../../lib/urlState";
import { DemandTable } from "../../components/DemandTable";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { DYNAMIC_PRESETS } from "./presets";
import { TeachingDrawer } from "./TeachingDrawer";

const PLAN_LABELS: Record<PlanName, string> = {
  wagner_whitin: "Wagner–Whitin",
  silver_meal: "Silver–Meal",
  lot_for_lot: "Lot-for-lot",
};
const PLAN_ORDER: PlanName[] = ["wagner_whitin", "silver_meal", "lot_for_lot"];

export function DynamicView({
  inputs,
  onInputs,
}: {
  inputs: DynamicInputs;
  onInputs: (next: DynamicInputs) => void;
}) {
  const [result, setResult] = useState<DynamicResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<PlanName>("wagner_whitin");
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<DynamicResponse>("/lot-sizing/dynamic", {
      demands: debounced.demands,
      setup_cost: debounced.setupCost,
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

  const best = result?.plans.wagner_whitin;
  const plan = result?.plans[selected];
  const orderPeriods = best
    ? best.orders.flatMap((q, i) => (q > 0 ? [i + 1] : [])).join(", ")
    : "";
  const periods = inputs.demands.map((_, i) => i + 1);

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Lot Sizing</h1>
          <div className="subtitle module-sub">
            Balance setup costs against holding inventory.
          </div>
        </div>
        <DemandTable
          label="Demand per period"
          values={inputs.demands}
          onChange={(demands) => onInputs({ ...inputs, demands })}
        />
        <div className="row">
          <NumberField
            label="Setup S"
            value={inputs.setupCost}
            onChange={(setupCost) => onInputs({ ...inputs, setupCost })}
          />
          <NumberField
            label="Holding h"
            value={inputs.holdingCost}
            onChange={(holdingCost) => onInputs({ ...inputs, holdingCost })}
          />
        </div>
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = DYNAMIC_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(DYNAMIC_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {best && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                Best plan — Wagner–Whitin (optimal)
              </div>
              <div className="hero-value">
                {formatMoney(best.total_cost)}{" "}
                <span className="hero-detail">
                  total cost · {best.setups} setups · orders in t = {orderPeriods}
                </span>
              </div>
            </div>
            <div className="hero-orders">
              {best.orders.map((q) => (q > 0 ? q : "—")).join(" · ")}
            </div>
          </div>
        )}
        {result && best && (
          <div className="row">
            {PLAN_ORDER.map((name) => (
              <MetricCard
                key={name}
                label={PLAN_LABELS[name]}
                value={formatMoney(result.plans[name].total_cost)}
                detail={
                  name === "wagner_whitin" ? (
                    <span style={{ color: "var(--accent)" }}>optimal ✓</span>
                  ) : (
                    percentGap(result.plans[name].total_cost, best.total_cost)
                  )
                }
                selected={selected === name}
                onClick={() => setSelected(name)}
              />
            ))}
          </div>
        )}
        {plan && (
          <PlotCard
            label={`${PLAN_LABELS[selected]} — orders vs demand, with ending inventory`}
            data={[
              { type: "bar", x: periods, y: inputs.demands, name: "Demand", marker: { color: "#e6eaee" } },
              { type: "bar", x: periods, y: plan.orders, name: "Order", marker: { color: "#0d9488" } },
              {
                type: "scatter",
                x: periods,
                y: plan.ending_inventory,
                name: "Ending inventory",
                mode: "lines+markers",
                line: { color: "#f59e0b" },
              },
            ]}
            layout={{ barmode: "group", xaxis: { dtick: 1, title: { text: "period" } } }}
          />
        )}
        {result && <TeachingDrawer steps={result.steps} />}
      </div>
    </>
  );
}
