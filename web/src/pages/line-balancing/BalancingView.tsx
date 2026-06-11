import { useEffect, useState } from "react";
import { ApiError, postJson } from "../../lib/api";
import type { BalancingResponse, HeuristicName } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { ganttTraces } from "../../lib/gantt";
import { useDebouncedValue } from "../../lib/useDebouncedValue";
import type { BalancingInputs } from "../../lib/urlState";
import { MetricCard } from "../../components/MetricCard";
import { NumberField } from "../../components/NumberField";
import { PlotCard } from "../../components/PlotCard";
import { precedenceTraces } from "./diagram";
import { BALANCING_PRESETS } from "./presets";
import { RpwDrawer } from "./RpwDrawer";
import { TasksTable } from "./TasksTable";

const LABELS: Record<HeuristicName, string> = {
  lcr: "LCR",
  rpw: "RPW",
  kilbridge_wester: "Kilbridge–Wester",
};
const ORDER: HeuristicName[] = ["lcr", "rpw", "kilbridge_wester"];

export function BalancingView({
  inputs,
  onInputs,
}: {
  inputs: BalancingInputs;
  onInputs: (next: BalancingInputs) => void;
}) {
  const [result, setResult] = useState<BalancingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<HeuristicName>("rpw");
  const debounced = useDebouncedValue(inputs);

  useEffect(() => {
    let cancelled = false;
    postJson<BalancingResponse>("/line-balancing/solve", {
      tasks: debounced.tasks.map((t) => ({
        id: t.id,
        duration: t.duration,
        predecessors: t.predecessors,
      })),
      cycle_time: debounced.cycleTime,
      available_time: debounced.availableTime,
      demand: debounced.demand,
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

  const demandMode = inputs.cycleTime === null;
  // best = fewest stations, then smoothest; ties keep the earlier heuristic
  const bestName = result
    ? ORDER.reduce((a, b) => {
        const ra = result.heuristics[a];
        const rb = result.heuristics[b];
        const better =
          rb.num_stations < ra.num_stations ||
          (rb.num_stations === ra.num_stations &&
            rb.smoothness_index < ra.smoothness_index);
        return better ? b : a;
      })
    : null;
  const best = bestName ? result!.heuristics[bestName] : null;
  const plan = result?.heuristics[selected];

  const durations = new Map(inputs.tasks.map((t) => [t.id, t.duration]));
  const stationRows = (plan?.stations ?? []).map((s) => {
    let clock = 0;
    return {
      label: `Station ${s.index}`,
      jobs: s.task_ids.map((id) => {
        const d = durations.get(id) ?? 0;
        const segment = { id, start: clock, end: clock + d };
        clock += d;
        return segment;
      }),
    };
  });

  return (
    <>
      <div className="input-panel">
        <div>
          <h1>Line Balancing</h1>
          <div className="subtitle module-sub">
            Split assembly work into stations that keep pace with demand.
          </div>
        </div>
        <TasksTable tasks={inputs.tasks} onChange={(tasks) => onInputs({ ...inputs, tasks })} />
        <div>
          <div className="label" style={{ marginBottom: 6 }}>Cycle time</div>
          <div className="mode-pills">
            <button
              className={demandMode ? "" : "active"}
              onClick={() =>
                onInputs({ ...inputs, cycleTime: 10, availableTime: null, demand: null })
              }
            >
              Given
            </button>
            <button
              className={demandMode ? "active" : ""}
              onClick={() =>
                onInputs({ ...inputs, cycleTime: null, availableTime: 480, demand: 60 })
              }
            >
              From demand
            </button>
          </div>
        </div>
        {demandMode ? (
          <div className="row">
            <NumberField
              label="Available time"
              value={inputs.availableTime ?? 0}
              onChange={(availableTime) => onInputs({ ...inputs, availableTime })}
            />
            <NumberField
              label="Demand"
              value={inputs.demand ?? 0}
              onChange={(demand) => onInputs({ ...inputs, demand })}
            />
          </div>
        ) : (
          <NumberField
            label="Cycle time CT"
            value={inputs.cycleTime ?? 0}
            onChange={(cycleTime) => onInputs({ ...inputs, cycleTime })}
          />
        )}
        {error && <div className="error-text">{error}</div>}
        <div style={{ marginTop: "auto" }}>
          <div className="label" style={{ marginBottom: 4 }}>Examples</div>
          <select
            value=""
            onChange={(e) => {
              const preset = BALANCING_PRESETS[e.target.value];
              if (preset) onInputs(preset);
            }}
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {Object.keys(BALANCING_PRESETS).map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="results-pane">
        {result && best && bestName && (
          <div className="card hero-card">
            <div>
              <div className="label" style={{ color: "var(--accent)" }}>
                Best balance — {LABELS[bestName]}
              </div>
              <div className="hero-value">
                {best.num_stations} stations{" "}
                <span className="hero-detail">
                  efficiency {formatNumber(best.efficiency * 100)}% · theoretical
                  minimum {result.min_stations} · CT {formatNumber(result.cycle_time)}
                  {demandMode ? " (from demand, rounded down)" : ""}
                </span>
              </div>
            </div>
            <div className="hero-orders">
              {best.stations.map((s) => s.task_ids.join(" ")).join("  ·  ")}
            </div>
          </div>
        )}
        {result && (
          <div className="row">
            {ORDER.map((name) => (
              <MetricCard
                key={name}
                label={LABELS[name]}
                value={`${result.heuristics[name].num_stations} stations`}
                detail={`${formatNumber(result.heuristics[name].efficiency * 100)}% efficient · SI ${formatNumber(result.heuristics[name].smoothness_index)}`}
                selected={selected === name}
                onClick={() => setSelected(name)}
              />
            ))}
          </div>
        )}
        {result && (
          <PlotCard
            label="Precedence diagram — columns are Kilbridge levels"
            data={precedenceTraces(inputs.tasks, result.columns)}
            layout={{
              xaxis: { dtick: 1, title: { text: "column" }, zeroline: false },
              yaxis: { visible: false },
            }}
            height={220}
          />
        )}
        {plan && result && (
          <PlotCard
            label={`${LABELS[selected]} stations — dotted line is the cycle time`}
            data={ganttTraces(stationRows)}
            layout={{
              barmode: "overlay",
              xaxis: { title: { text: "time in station" } },
              yaxis: { autorange: "reversed" },
              shapes: [
                {
                  type: "line",
                  x0: result.cycle_time,
                  x1: result.cycle_time,
                  yref: "paper",
                  y0: 0,
                  y1: 1,
                  line: { color: "#dc2626", width: 1.5, dash: "dot" },
                },
              ],
            }}
            height={200}
          />
        )}
        {result && <RpwDrawer steps={result.steps} />}
      </div>
    </>
  );
}
