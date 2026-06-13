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

type AnyPlanName = PlanName | "wagner_whitin_backlog";

const PLAN_LABELS: Record<AnyPlanName, string> = {
  wagner_whitin: "Wagner–Whitin",
  silver_meal: "Silver–Meal",
  lot_for_lot: "Lot-for-lot",
  wagner_whitin_backlog: "WW + backlog",
};
const BASE_ORDER: PlanName[] = ["wagner_whitin", "silver_meal", "lot_for_lot"];

export function DynamicView({
  inputs,
  onInputs,
}: {
  inputs: DynamicInputs;
  onInputs: (next: DynamicInputs) => void;
}) {
  const [result, setResult] = useState<DynamicResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<AnyPlanName>("wagner_whitin");
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<DynamicResponse>("/lot-sizing/dynamic", {
      demands: debounced.demands,
      setup_cost: debounced.setupCost,
      holding_cost: debounced.holdingCost,
      backlog_cost: debounced.backlogCost ?? null,
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

  // when a backlog penalty is set, the backlog-aware plan is the true optimum
  const best = result ? (result.plans.wagner_whitin_backlog ?? result.plans.wagner_whitin) : undefined;
  const bestName: AnyPlanName = result?.plans.wagner_whitin_backlog
    ? "wagner_whitin_backlog"
    : "wagner_whitin";
  const presentPlans: AnyPlanName[] = result
    ? [...BASE_ORDER, ...(result.plans.wagner_whitin_backlog ? ["wagner_whitin_backlog" as const] : [])]
    : [];
  // the selected plan can disappear when the backlog penalty is removed
  const activeSelected: AnyPlanName = result?.plans[selected] ? selected : "wagner_whitin";
  const plan = result?.plans[activeSelected];
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
        <NumberField
          label="Backlog b (0 = shortages not allowed)"
          value={inputs.backlogCost ?? 0}
          onChange={(backlogCost) =>
            onInputs({ ...inputs, backlogCost: backlogCost > 0 ? backlogCost : undefined })
          }
        />
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
                Best plan — {PLAN_LABELS[bestName]} (optimal
                {bestName === "wagner_whitin_backlog" ? ", backorders allowed" : ""})
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
            {presentPlans.map((name) => (
              <MetricCard
                key={name}
                label={PLAN_LABELS[name]}
                value={formatMoney(result.plans[name]!.total_cost)}
                detail={
                  name === bestName ? (
                    <span style={{ color: "var(--accent)" }}>optimal ✓</span>
                  ) : (
                    percentGap(result.plans[name]!.total_cost, best.total_cost)
                  )
                }
                selected={activeSelected === name}
                onClick={() => setSelected(name)}
              />
            ))}
          </div>
        )}
        {plan && (
          <PlotCard
            label={`${PLAN_LABELS[activeSelected]} — orders vs demand; inventory below 0 is backordered`}
            data={[
              { type: "bar", x: periods, y: inputs.demands, name: "Demand", marker: { color: "#e6eaee" } },
              { type: "bar", x: periods, y: plan.orders, name: "Order", marker: { color: "#0d9488" } },
              {
                type: "scatter",
                x: periods,
                y: plan.ending_inventory,
                name: "End inventory (− = backorder)",
                mode: "lines+markers",
                line: { color: "#f59e0b" },
              },
            ]}
            layout={{
              barmode: "group",
              xaxis: { dtick: 1, title: { text: "period" } },
              shapes: [
                {
                  type: "line",
                  xref: "paper",
                  x0: 0,
                  x1: 1,
                  y0: 0,
                  y1: 0,
                  line: { color: "#101418", width: 1, dash: "dot" },
                },
              ],
            }}
          />
        )}
        {result && <TeachingDrawer steps={result.steps} />}
      </div>
    </>
  );
}
