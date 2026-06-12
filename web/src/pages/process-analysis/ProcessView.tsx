import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { ProcessResponse } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { ProcessInputs } from "../../lib/urlState";
import { JobsTable } from "../../components/JobsTable";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { BottleneckDrawer } from "./BottleneckDrawer";
import { capacityTrace, perHour, utilizationTrace } from "./charts";
import { PROCESS_PRESETS } from "./presets";

export function ProcessView({
  inputs,
  onInputs,
}: {
  inputs: ProcessInputs;
  onInputs: (next: ProcessInputs) => void;
}) {
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<ProcessResponse>("/process-analysis/solve", {
      resources: debounced.resources.map((r) => ({
        name: r.name,
        processing_time: r.timeMin,
        servers: r.servers,
      })),
      // UI speaks units/hour; core and the API are per-minute
      demand: debounced.demandPerHour === null ? null : debounced.demandPerHour / 60,
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

  const demandKnown = inputs.demandPerHour !== null;
  const names = result?.resources.map((r) => r.name) ?? [];

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Process Analysis</h1>
          <div className="subtitle module-sub">
            Find the bottleneck — the step that sets the pace for everything.
          </div>
        </div>
        <JobsTable
          label="Process steps, in order (minutes/unit, servers)"
          idLabel="resource"
          columns={["min/unit", "servers"]}
          rows={inputs.resources.map((r) => ({ id: r.name, a: r.timeMin, b: r.servers }))}
          onChange={(rows) =>
            onInputs({
              ...inputs,
              resources: rows.map((row) => ({ name: row.id, timeMin: row.a, servers: row.b })),
            })
          }
        />
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Demand</div>
          <div className="mode-pills">
            <button
              className={demandKnown ? "active" : ""}
              onClick={() => onInputs({ ...inputs, demandPerHour: 30 })}
            >
              Known
            </button>
            <button
              className={demandKnown ? "" : "active"}
              onClick={() => onInputs({ ...inputs, demandPerHour: null })}
            >
              Capacity only
            </button>
          </div>
        </div>
        {demandKnown && (
          <NumberField
            label="Demand (units/hour)"
            value={inputs.demandPerHour ?? 0}
            onChange={(demandPerHour) => onInputs({ ...inputs, demandPerHour })}
          />
        )}
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = PROCESS_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(PROCESS_PRESETS).map((name) => (
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
                Bottleneck — the slowest resource sets the pace
              </div>
              <div className="hero-value">
                {result.bottleneck}{" "}
                <span className="hero-detail">
                  capacity {perHour(result.process_capacity)} /h · flow rate{" "}
                  {perHour(result.flow_rate)} /h · {result.constraint}-constrained
                </span>
              </div>
            </div>
            <div className="hero-orders">
              flow rate = min(demand, bottleneck capacity)
            </div>
          </div>
        )}
        {result && (
          <div className="row">
            <MetricCard
              label="Process capacity"
              value={`${perHour(result.process_capacity)} /h`}
              detail="the bottleneck's capacity"
            />
            <MetricCard
              label="Flow rate"
              value={`${perHour(result.flow_rate)} /h`}
              detail={`${result.constraint}-constrained`}
            />
            <MetricCard
              label="Flow time (no waiting)"
              value={`${formatNumber(result.unloaded_flow_time)} min`}
              detail="sum of processing times"
            />
          </div>
        )}
        {result && (
          <PlotCard
            label="Capacity per resource (units/hour) — red bar is the bottleneck"
            data={[capacityTrace(result.resources, result.bottleneck)]}
            layout={{
              yaxis: { title: { text: "units/hour" } },
              shapes:
                inputs.demandPerHour === null
                  ? []
                  : [
                      {
                        type: "line",
                        xref: "paper",
                        x0: 0,
                        x1: 1,
                        y0: inputs.demandPerHour,
                        y1: inputs.demandPerHour,
                        line: { color: "#101418", width: 1.5, dash: "dot" },
                      },
                    ],
            }}
            height={240}
          />
        )}
        {result && (
          <div className="row">
            <div style={{ flex: 1, minWidth: 0 }}>
              <PlotCard
                label="Utilization (flow rate / capacity)"
                data={[utilizationTrace(names, result.resources.map((r) => r.utilization))]}
                layout={{
                  xaxis: { range: [0, 130], title: { text: "%" } },
                  yaxis: { autorange: "reversed" },
                  shapes: [
                    {
                      type: "line",
                      yref: "paper",
                      x0: 100,
                      x1: 100,
                      y0: 0,
                      y1: 1,
                      line: { color: "#8a94a0", width: 1, dash: "dot" },
                    },
                  ],
                }}
                height={90 + 36 * names.length}
              />
            </div>
            {demandKnown && (
              <div style={{ flex: 1, minWidth: 0 }}>
                <PlotCard
                  label="Implied utilization (demand / capacity) — past 100% is overload"
                  data={[
                    utilizationTrace(
                      names,
                      result.resources.map((r) => r.implied_utilization ?? 0),
                    ),
                  ]}
                  layout={{
                    xaxis: {
                      range: [
                        0,
                        Math.max(
                          130,
                          ...result.resources.map((r) => (r.implied_utilization ?? 0) * 115),
                        ),
                      ],
                      title: { text: "%" },
                    },
                    yaxis: { autorange: "reversed" },
                    shapes: [
                      {
                        type: "line",
                        yref: "paper",
                        x0: 100,
                        x1: 100,
                        y0: 0,
                        y1: 1,
                        line: { color: "#8a94a0", width: 1, dash: "dot" },
                      },
                    ],
                  }}
                  height={90 + 36 * names.length}
                />
              </div>
            )}
          </div>
        )}
        {result && <BottleneckDrawer steps={result.steps} />}
      </div>
    </>
  );
}
