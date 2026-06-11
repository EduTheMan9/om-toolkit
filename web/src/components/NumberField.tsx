export function NumberField({
  label,
  value,
  onChange,
  min = 0,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min?: number;
}) {
  return (
    <div style={{ flex: 1 }}>
      <div className="label" style={{ marginBottom: 4 }}>{label}</div>
      <input
        type="number"
        value={Number.isNaN(value) ? "" : value}
        min={min}
        step="any"
        onChange={(e) => onChange(e.target.valueAsNumber)}
      />
    </div>
  );
}
