import type { ReactNode } from "react";

export function MetricCard({
  label,
  value,
  detail,
  selected = false,
  onClick,
}: {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <div
      className="card"
      onClick={onClick}
      style={{
        padding: "10px 14px",
        flex: 1,
        cursor: onClick ? "pointer" : undefined,
        borderColor: selected ? "var(--accent)" : undefined,
        borderWidth: selected ? 1.5 : 1,
      }}
    >
      <div className="label">{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700 }}>
        {value}
      </div>
      {detail && <div style={{ fontSize: 11, color: "var(--subtle)" }}>{detail}</div>}
    </div>
  );
}
