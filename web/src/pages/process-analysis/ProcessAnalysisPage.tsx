import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeProcess, encodeProcess } from "../../lib/urlState";
import type { ProcessInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { PROCESS_PRESETS } from "./presets";
import { ProcessView } from "./ProcessView";
import { LITTLES_DEFAULTS, LittlesView } from "./LittlesView";
import type { LittlesInputs } from "./LittlesView";

export default function ProcessAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<"capacity" | "littles">(
    searchParams.get("mode") === "littles" ? "littles" : "capacity",
  );
  const [inputs, setInputs] = useState<ProcessInputs>(
    () =>
      decodeProcess("?" + searchParams.toString()) ??
      PROCESS_PRESETS["Sandwich line"],
  );
  const [littles, setLittles] = useState<LittlesInputs>(LITTLES_DEFAULTS);

  const update = (next: ProcessInputs) => {
    setInputs(next);
    setSearchParams(encodeProcess(next), { replace: true });
  };

  const switchMode = (next: "capacity" | "littles") => {
    setMode(next);
    setSearchParams(next === "littles" ? "mode=littles" : encodeProcess(inputs), {
      replace: true,
    });
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button
          className={mode === "capacity" ? "active" : ""}
          onClick={() => switchMode("capacity")}
        >
          Capacity & bottleneck
        </button>
        <button
          className={mode === "littles" ? "active" : ""}
          onClick={() => switchMode("littles")}
        >
          Little's Law
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "capacity" ? (
          <ProcessView inputs={inputs} onInputs={update} />
        ) : (
          <LittlesView inputs={littles} onInputs={setLittles} />
        )}
      </div>
    </div>
  );
}
