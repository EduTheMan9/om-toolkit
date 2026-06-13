import "./DemandTable.css";

export interface JobRow {
  id: string;
  a: number;
  b: number;
  c?: number; // optional third numeric column (e.g. job weight)
}

/** Editable job table: text ID + two or three numeric columns (headers via
 * props). Pasting a column from Excel/Sheets into a numeric cell fills
 * downward, same convention as DemandTable (capped at the existing rows — new
 * jobs need an ID, so paste can't invent them). */
export function JobsTable({
  label,
  idLabel = "job",
  columns,
  rows,
  onChange,
}: {
  label: string;
  idLabel?: string;
  columns: [string, string] | [string, string, string];
  rows: JobRow[];
  onChange: (next: JobRow[]) => void;
}) {
  const keys = (columns.length === 3 ? ["a", "b", "c"] : ["a", "b"]) as ("a" | "b" | "c")[];

  const setRow = (i: number, patch: Partial<JobRow>) => {
    const next = [...rows];
    next[i] = { ...next[i], ...patch };
    onChange(next);
  };

  const handlePaste = (i: number, key: "a" | "b" | "c", e: React.ClipboardEvent) => {
    const pasted = e.clipboardData
      .getData("text")
      .split(/[\s,;]+/)
      .filter((t) => t.length > 0)
      .map(Number);
    if (pasted.length < 2 || pasted.some(Number.isNaN)) return; // normal paste
    e.preventDefault();
    const next = [...rows];
    pasted.forEach((v, k) => {
      if (i + k < next.length) next[i + k] = { ...next[i + k], [key]: v };
    });
    onChange(next);
  };

  const addRow = () => {
    const prefix = idLabel.charAt(0).toUpperCase();
    let n = rows.length + 1;
    while (rows.some((r) => r.id === `${prefix}${n}`)) n += 1;
    const blank: JobRow = { id: `${prefix}${n}`, a: 1, b: 1 };
    if (columns.length === 3) blank.c = 1;
    onChange([...rows, blank]);
  };

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>{label}</div>
      <table className="demand-table">
        <thead>
          <tr>
            <th>{idLabel}</th>
            {columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              <td style={{ width: 56 }}>
                <input
                  value={row.id}
                  onChange={(e) => setRow(i, { id: e.target.value })}
                />
              </td>
              {keys.map((key) => (
                <td key={key}>
                  <input
                    type="number"
                    step="any"
                    min={0}
                    value={row[key] === undefined || Number.isNaN(row[key]) ? "" : row[key]}
                    onChange={(e) => setRow(i, { [key]: e.target.valueAsNumber })}
                    onPaste={(e) => handlePaste(i, key, e)}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="demand-table-actions">
        <button onClick={addRow}>+ {idLabel}</button>
        <button onClick={() => rows.length > 1 && onChange(rows.slice(0, -1))}>
          − {idLabel}
        </button>
      </div>
      <div className="demand-table-hint">tip: paste a column straight from Excel</div>
    </div>
  );
}
