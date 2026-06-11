import "../../components/DemandTable.css";
import type { BalancingTask } from "../../lib/urlState";

const parsePreds = (text: string): string[] =>
  text.split(/[\s,.;]+/).filter((p) => p.length > 0);

export function TasksTable({
  tasks,
  onChange,
}: {
  tasks: BalancingTask[];
  onChange: (next: BalancingTask[]) => void;
}) {
  const setTask = (i: number, patch: Partial<BalancingTask>) => {
    const next = [...tasks];
    next[i] = { ...next[i], ...patch };
    onChange(next);
  };

  const addTask = () => {
    const used = new Set(tasks.map((t) => t.id));
    let id = `T${tasks.length + 1}`;
    for (let i = 0; i < 26; i++) {
      const letter = String.fromCharCode(65 + i);
      if (!used.has(letter)) {
        id = letter;
        break;
      }
    }
    onChange([...tasks, { id, duration: 1, predecessors: [] }]);
  };

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>
        Tasks (duration, predecessors)
      </div>
      <table className="demand-table">
        <thead>
          <tr>
            <th>task</th>
            <th>time</th>
            <th>preds</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t, i) => (
            <tr key={i}>
              <td style={{ width: 48 }}>
                <input value={t.id} onChange={(e) => setTask(i, { id: e.target.value })} />
              </td>
              <td style={{ width: 64 }}>
                <input
                  type="number"
                  step="any"
                  min={0}
                  value={Number.isNaN(t.duration) ? "" : t.duration}
                  onChange={(e) => setTask(i, { duration: e.target.valueAsNumber })}
                />
              </td>
              <td>
                <input
                  value={t.predecessors.join(",")}
                  placeholder="—"
                  onChange={(e) => setTask(i, { predecessors: parsePreds(e.target.value) })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="demand-table-actions">
        <button onClick={addTask}>+ task</button>
        <button onClick={() => tasks.length > 1 && onChange(tasks.slice(0, -1))}>
          − task
        </button>
      </div>
      <div className="demand-table-hint">preds: comma-separated task IDs</div>
    </div>
  );
}
