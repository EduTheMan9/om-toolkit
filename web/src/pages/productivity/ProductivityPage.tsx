import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeProductivity, encodeProductivity } from "../../lib/urlState";
import type { ProductivityInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { CompareView } from "./CompareView";
import { OeeView } from "./OeeView";
import { SingleFactorView } from "./SingleFactorView";
import { PRODUCTIVITY_PRESETS } from "./presets";

type Mode = "compare" | "single" | "oee";

export default function ProductivityPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<Mode>(() => {
    const m = searchParams.get("mode");
    return m === "single" || m === "oee" ? m : "compare";
  });
  const [inputs, setInputs] = useState<ProductivityInputs>(
    () =>
      decodeProductivity("?" + searchParams.toString()) ??
      PRODUCTIVITY_PRESETS["Bakery, two weeks"],
  );

  const update = (next: ProductivityInputs) => {
    setInputs(next);
    setSearchParams(encodeProductivity(next), { replace: true });
  };

  const switchMode = (next: Mode) => {
    setMode(next);
    setSearchParams(next === "compare" ? encodeProductivity(inputs) : `mode=${next}`, {
      replace: true,
    });
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button
          className={mode === "compare" ? "active" : ""}
          onClick={() => switchMode("compare")}
        >
          Two-period comparison
        </button>
        <button
          className={mode === "single" ? "active" : ""}
          onClick={() => switchMode("single")}
        >
          Single-factor calculator
        </button>
        <button
          className={mode === "oee" ? "active" : ""}
          onClick={() => switchMode("oee")}
        >
          OEE
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "compare" && <CompareView inputs={inputs} onInputs={update} />}
        {mode === "single" && <SingleFactorView />}
        {mode === "oee" && <OeeView />}
      </div>
    </div>
  );
}
