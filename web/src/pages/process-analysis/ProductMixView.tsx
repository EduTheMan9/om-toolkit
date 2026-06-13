import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { ProductMixResponse } from "../../lib/api";
import { formatMoney, formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import { JobsTable } from "../../components/JobsTable";
import { NumberField } from "../../components/NumberField";
import { ProductMixDrawer } from "./ProductMixDrawer";

export interface ProductRow {
  name: string;
  margin: number;
  bottleneckTime: number;
  demand: number;
}

export interface ProductMixInputs {
  products: ProductRow[];
  availableMinutes: number;
}

// The worked example from tests/test_product_mix.py: P1 has the highest unit
// margin yet is made last and only half — the TOC lesson.
export const PRODUCT_MIX_DEFAULTS: ProductMixInputs = {
  products: [
    { name: "P1", margin: 30, bottleneckTime: 10, demand: 100 },
    { name: "P2", margin: 24, bottleneckTime: 6, demand: 100 },
    { name: "P3", margin: 20, bottleneckTime: 4, demand: 100 },
  ],
  availableMinutes: 1500,
};

/** Theory of Constraints product mix: rank products by contribution per
 * bottleneck-minute and fill the scarce minutes greedily. */
export function ProductMixView({
  inputs,
  onInputs,
}: {
  inputs: ProductMixInputs;
  onInputs: (next: ProductMixInputs) => void;
}) {
  const [result, setResult] = useState<ProductMixResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<ProductMixResponse>("/process-analysis/product-mix", {
      available_minutes: debounced.availableMinutes,
      products: debounced.products.map((p) => ({
        name: p.name,
        contribution_margin: p.margin,
        bottleneck_time: p.bottleneckTime,
        demand: p.demand,
      })),
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

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Product mix</h1>
          <div className="subtitle module-sub">
            One bottleneck, several products — which mix makes the most money?
            Rank by contribution per scarce minute, not per unit.
          </div>
        </div>
        <JobsTable
          label="Products (margin $/u, bottleneck min/u, demand)"
          idLabel="product"
          columns={["$/u", "min/u", "demand"]}
          rows={inputs.products.map((p) => ({
            id: p.name,
            a: p.margin,
            b: p.bottleneckTime,
            c: p.demand,
          }))}
          onChange={(rows) =>
            onInputs({
              ...inputs,
              products: rows.map((r) => ({
                name: r.id,
                margin: r.a,
                bottleneckTime: r.b,
                demand: r.c ?? 0,
              })),
            })
          }
        />
        <NumberField
          label="Bottleneck time available (min)"
          value={inputs.availableMinutes}
          onChange={(availableMinutes) => onInputs({ ...inputs, availableMinutes })}
        />
        {error && <div className="error-text">{error}</div>}
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  Most profitable mix — contribution per bottleneck-minute
                </div>
                <div className="hero-value">
                  {formatMoney(result.total_contribution)}{" "}
                  <span className="hero-detail">
                    total contribution · {formatNumber(result.idle_minutes)} min idle
                  </span>
                </div>
              </div>
              <div className="hero-orders">rank by $ ÷ min/u</div>
            </div>
            <div className="card" style={{ padding: "12px 14px" }}>
              <div className="label">Make, in priority order</div>
              <table style={{ width: "100%", fontSize: 12, borderSpacing: 0, marginTop: 6 }}>
                <thead>
                  <tr style={{ textAlign: "left", color: "var(--subtle)" }}>
                    <th style={{ paddingBottom: 4 }}>product</th>
                    <th>$/min</th>
                    <th>make</th>
                    <th>min used</th>
                    <th>contribution</th>
                    <th>limited by</th>
                  </tr>
                </thead>
                <tbody>
                  {result.allocations.map((a) => (
                    <tr key={a.name}>
                      <td style={{ padding: "3px 0" }}>{a.name}</td>
                      <td>{formatNumber(a.ratio)}</td>
                      <td>{formatNumber(a.units)}</td>
                      <td>{formatNumber(a.minutes)}</td>
                      <td>{formatMoney(a.contribution)}</td>
                      <td className={a.limited_by === "capacity" ? "step-bad" : ""}>
                        {a.limited_by}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="subtitle" style={{ fontSize: 11, marginTop: 6 }}>
                A product limited by <b>capacity</b> ran out of bottleneck time
                before its demand — the next scarce minute would be worth more
                spent here than anywhere below it.
              </div>
            </div>
            <ProductMixDrawer steps={result.steps} />
          </>
        )}
      </div>
    </>
  );
}
