import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeProductivity, encodeProductivity } from "../../lib/urlState";
import type { ProductivityInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { CompareView } from "./CompareView";
import { SingleFactorView } from "./SingleFactorView";
import { PRODUCTIVITY_PRESETS } from "./presets";

export default function ProductivityPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<"compare" | "single">(
    searchParams.get("mode") === "single" ? "single" : "compare",
  );
  const [inputs, setInputs] = useState<ProductivityInputs>(
    () =>
      decodeProductivity("?" + searchParams.toString()) ??
      PRODUCTIVITY_PRESETS["Bakery, two weeks"],
  );

  const update = (next: ProductivityInputs) => {
    setInputs(next);
    setSearchParams(encodeProductivity(next), { replace: true });
  };

  const switchMode = (next: "compare" | "single") => {
    setMode(next);
    setSearchParams(next === "single" ? "mode=single" : encodeProductivity(inputs), {
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
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "compare" ? (
          <CompareView inputs={inputs} onInputs={update} />
        ) : (
          <SingleFactorView />
        )}
      </div>
    </div>
  );
}
