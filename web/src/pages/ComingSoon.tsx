import { useLocation } from "react-router-dom";
import { MODULES } from "../modules";

export default function ComingSoon() {
  const { pathname } = useLocation();
  const mod = MODULES.find((m) => m.path === pathname);
  return (
    <div style={{ padding: "48px 56px" }}>
      <h1 style={{ fontSize: 24 }}>{mod?.name ?? "Module"}</h1>
      <p className="subtitle" style={{ marginTop: 8 }}>
        This module hasn't been rebuilt yet — it's still available in the
        classic Streamlit app while the redesign rolls out module by module.
      </p>
    </div>
  );
}
