import "./MatrixEditor.css";

/** Editable binary incidence matrix: rows = machines, columns = parts.
 * Click a cell to toggle whether the part visits the machine. A freshly
 * added all-zero machine/part triggers core's "remove it" message inline,
 * which tells the user exactly what to do next. */
export function MatrixEditor({
  matrix,
  onChange,
}: {
  matrix: number[][];
  onChange: (next: number[][]) => void;
}) {
  const nParts = matrix[0]?.length ?? 0;

  const toggle = (i: number, j: number) =>
    onChange(
      matrix.map((row, r) =>
        r === i ? row.map((v, c) => (c === j ? 1 - v : v)) : row,
      ),
    );

  return (
    <div>
      <div className="label" style={{ marginBottom: 6 }}>
        Incidence matrix — tick where the part visits the machine
      </div>
      <table className="matrix-editor">
        <thead>
          <tr>
            <th />
            {Array.from({ length: nParts }, (_, j) => (
              <th key={j}>P{j + 1}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={i}>
              <th>M{i + 1}</th>
              {row.map((v, j) => (
                <td key={j}>
                  <button
                    className={v ? "on" : ""}
                    aria-label={`M${i + 1} × P${j + 1}`}
                    onClick={() => toggle(i, j)}
                  >
                    {v ? "1" : ""}
                  </button>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="matrix-editor-actions">
        <button onClick={() => onChange([...matrix, matrix[0].map(() => 0)])}>
          + machine
        </button>
        <button onClick={() => matrix.length > 1 && onChange(matrix.slice(0, -1))}>
          − machine
        </button>
        <button onClick={() => onChange(matrix.map((row) => [...row, 0]))}>
          + part
        </button>
        <button onClick={() => nParts > 1 && onChange(matrix.map((row) => row.slice(0, -1)))}>
          − part
        </button>
      </div>
    </div>
  );
}
