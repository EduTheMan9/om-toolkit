import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { DispatchMethodName, DispatchResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { ganttTraces } from "../../lib/gantt";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { DispatchJob } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { PlotCard } from "../../components/PlotCard";
import { DISPATCH_PRESETS } from "./presets";
import "./Scheduling.css";

const METHOD_INFO: Record<DispatchMethodName, { label: string; note: string }> = {
  fcfs: { label: "FCFS", note: "first come, first served — the no-thought baseline" },
  spt: { label: "SPT", note: "shortest first — provably minimizes avg completion" },
  wspt: { label: "WSPT", note: "shortest weighted (p/w) — minimizes Σ w·completion" },
  edd: { label: "EDD", note: "earliest due date — minimizes the worst lateness" },
  lpt: { label: "LPT", note: "longest first — usually the cautionary tale" },
  moore_hodgson: { label: "Moore–Hodgson", note: "provably the fewest tardy jobs" },
  min_total_tardiness: { label: "Min total tardiness", note: "exact optimum (subset DP)" },
};
const METHOD_ORDER: DispatchMethodName[] = [
  "fcfs", "spt", "wspt", "edd", "lpt", "moore_hodgson", "min_total_tardiness",
];

type MetricKey =
  | "avg_completion_time"
  | "weighted_completion_time"
  | "avg_tardiness"
  | "total_tardiness"
  | "max_tardiness"
  | "max_lateness"
  | "num_tardy";

const METRIC_COLUMNS: { key: MetricKey; label: string }[] = [
  { key: "avg_completion_time", label: "Avg completion" },
  { key: "weighted_completion_time", label: "Σ w·completion" },
  { key: "avg_tardiness", label: "Avg tardiness" },
  { key: "total_tardiness", label: "Total tardiness" },
  { key: "max_tardiness", label: "Max tardiness" },
  { key: "max_lateness", label: "Max lateness (Lₘₐₓ)" },
  { key: "num_tardy", label: "# tardy" },
];

export function DispatchView({
  jobs,
  onJobs,
}: {
  jobs: DispatchJob[];
  onJobs: (next: DispatchJob[]) => void;
}) {
  const [result, setResult] = useState<DispatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DispatchMethodName>("spt");
  const debounced = useDebouncedValue(jobs);

  useEffect(() => {
    let cancelled = false;
    postJson<DispatchResponse>("/scheduling/dispatch", {
      jobs: debounced.map((j) => ({
        id: j.id,
        processing_time: j.processingTime,
        due_date: j.dueDate,
        weight: j.weight,
      })),
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

  const methods = result?.methods ?? {};
  const present = METHOD_ORDER.filter((name) => methods[name]);
  // the selected method can disappear (DP row capped beyond 15 jobs)
  const active: DispatchMethodName = methods[selected] ? selected : "spt";
  const plan = methods[active];

  const due = new Map(jobs.map((j) => [j.id, j.dueDate]));
  const tardy = new Set(
    (plan?.schedule ?? [])
      .filter((s) => s.end > (due.get(s.id) ?? Infinity))
      .map((s) => s.id),
  );

  // lower is better for every column; highlight the per-column minimum
  const best: Partial<Record<MetricKey, number>> = {};
  for (const { key } of METRIC_COLUMNS) {
    best[key] = Math.min(...present.map((name) => methods[name]![key]));
  }

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Scheduling</h1>
          <div className="subtitle module-sub">
            One machine, n jobs — which order serves them best?
          </div>
        </div>
        <JobsTable
          label="Jobs (processing time, due date, weight)"
          columns={["p", "due", "w"]}
          rows={jobs.map((j) => ({ id: j.id, a: j.processingTime, b: j.dueDate, c: j.weight }))}
          onChange={(rows) =>
            onJobs(
              rows.map((r) => ({
                id: r.id,
                processingTime: r.a,
                dueDate: r.b,
                weight: r.c ?? 1,
              })),
            )
          }
        />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = DISPATCH_PRESETS[e.target.value];
              if (preset) onJobs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(DISPATCH_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {plan && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                {METHOD_INFO[active].label} — {METHOD_INFO[active].note}
              </div>
              <div className="hero-value">{plan.sequence.join(" → ")}</div>
            </div>
            <div className="hero-orders">
              {plan.num_tardy} tardy · avg completion {formatNumber(plan.avg_completion_time)}
            </div>
          </div>
        )}
        {result && (
          <div className="card" style={{ padding: "10px 14px" }}>
            <div className="label">
              Every rule on your jobs — click a row, best value per column in teal
            </div>
            <table className="compare-table">
              <thead>
                <tr>
                  <th>method</th>
                  {METRIC_COLUMNS.map((m) => (
                    <th key={m.key}>{m.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {present.map((name) => (
                  <tr
                    key={name}
                    className={active === name ? "selected" : ""}
                    onClick={() => setSelected(name)}
                  >
                    <td>
                      {METHOD_INFO[name].label}{" "}
                      <span className="method-note">{METHOD_INFO[name].note}</span>
                    </td>
                    {METRIC_COLUMNS.map((m) => (
                      <td
                        key={m.key}
                        className={methods[name]![m.key] === best[m.key] ? "best" : ""}
                      >
                        {formatNumber(methods[name]![m.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {result.optimal_capped && (
              <div className="subtitle" style={{ marginTop: 6, fontSize: 11 }}>
                Exact total-tardiness optimization is capped at 15 jobs (the
                search space doubles with each job) — that row is omitted.
              </div>
            )}
          </div>
        )}
        {plan && (
          <PlotCard
            label={`${METHOD_INFO[active].label} timeline — tardy jobs in red`}
            data={ganttTraces([{ label: "Machine", jobs: plan.schedule }], tardy)}
            layout={{
              barmode: "overlay",
              xaxis: { title: { text: "time" } },
              yaxis: { autorange: "reversed" },
            }}
            height={160}
          />
        )}
      </div>
    </>
  );
}
