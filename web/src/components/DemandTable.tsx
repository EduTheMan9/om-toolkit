import "./DemandTable.css";

/** Editable per-period numeric column. Pasting a column/range from
 * Excel/Sheets replaces values starting at the pasted-into row. */
export function DemandTable({
  label,
  values,
  onChange,
}: {
  label: string;
  values: number[];
  onChange: (next: number[]) => void;
}) {
  const setAt = (i: number, v: number) => {
    const next = [...values];
    next[i] = v;
    onChange(next);
  };

  const handlePaste = (i: number, e: React.ClipboardEvent) => {
    const pasted = e.clipboardData
      .getData("text")
      .split(/[\s,;]+/)
      .filter((t) => t.length > 0)
      .map(Number);
    if (pasted.length < 2 || pasted.some(Number.isNaN)) return; // normal paste
    e.preventDefault();
    const next = [...values];
    pasted.forEach((v, k) => {
      next[i + k] = v;
    });
    onChange(next);
  };

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>{label}</div>
      <table className="demand-table">
        <thead>
          <tr><th>t</th><th>demand</th></tr>
        </thead>
        <tbody>
          {values.map((v, i) => (
            <tr key={i}>
              <td className="idx">{i + 1}</td>
              <td>
                <input
                  type="number"
                  step="any"
                  min={0}
                  value={Number.isNaN(v) ? "" : v}
                  onChange={(e) => setAt(i, e.target.valueAsNumber)}
                  onPaste={(e) => handlePaste(i, e)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="demand-table-actions">
        <button onClick={() => onChange([...values, 0])}>+ period</button>
        <button onClick={() => values.length > 1 && onChange(values.slice(0, -1))}>
          − period
        </button>
      </div>
      <div className="demand-table-hint">tip: paste a column straight from Excel</div>
    </div>
  );
}
