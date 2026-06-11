import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { JohnsonResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { ganttTraces } from "../../lib/gantt";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { JohnsonJob } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { MetricCard } from "../../components/MetricCard";
import { PlotCard } from "../../components/PlotCard";
import { JOHNSON_PRESETS } from "./presets";
import { JohnsonDrawer } from "./JohnsonDrawer";

export function JohnsonView({
  jobs,
  onJobs,
}: {
  jobs: JohnsonJob[];
  onJobs: (next: JohnsonJob[]) => void;
}) {
  const [result, setResult] = useState<JohnsonResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(jobs);

  useEffect(() => {
    let cancelled = false;
    postJson<JohnsonResponse>("/scheduling/johnson", {
      jobs: debounced.map((j) => ({ id: j.id, time_m1: j.timeM1, time_m2: j.timeM2 })),
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

  const slower = result ? result.input_order_makespan - result.makespan : 0;

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Scheduling</h1>
          <div className="subtitle module-sub">
            Two machines in series — Johnson's rule finds the fastest order.
          </div>
        </div>
        <JobsTable
          label="Jobs (machine 1, machine 2 times)"
          columns={["M1", "M2"]}
          rows={jobs.map((j) => ({ id: j.id, a: j.timeM1, b: j.timeM2 }))}
          onChange={(rows) => onJobs(rows.map((r) => ({ id: r.id, timeM1: r.a, timeM2: r.b })))}
        />
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = JOHNSON_PRESETS[e.target.value];
              if (preset) onJobs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(JOHNSON_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {result && (
          <>
            <div className="card hero-card">
              <div>
                <div className="label" style={{ color: "var(--accent)" }}>
                  Optimal sequence — Johnson's rule
                </div>
                <div className="hero-value">
                  {result.sequence.join(" → ")}{" "}
                  <span className="hero-detail">makespan {formatNumber(result.makespan)}</span>
                </div>
              </div>
              <div className="hero-orders">
                all done at t = {formatNumber(result.makespan)}
              </div>
            </div>
            <div className="row">
              <MetricCard
                label="Johnson makespan"
                value={formatNumber(result.makespan)}
                detail={<span style={{ color: "var(--accent)" }}>optimal ✓</span>}
              />
              <MetricCard
                label="Input order makespan"
                value={formatNumber(result.input_order_makespan)}
                detail={slower > 0 ? `${formatNumber(slower)} slower` : "already optimal"}
              />
            </div>
            <PlotCard
              label="Two-machine Gantt — gaps on machine 2 are idle time"
              data={ganttTraces([
                { label: "Machine 1", jobs: result.machine1 },
                { label: "Machine 2", jobs: result.machine2 },
              ])}
              layout={{
                barmode: "overlay",
                xaxis: { title: { text: "time" } },
                yaxis: { autorange: "reversed" },
              }}
              height={200}
            />
            <JohnsonDrawer steps={result.steps} />
          </>
        )}
      </div>
    </>
  );
}
