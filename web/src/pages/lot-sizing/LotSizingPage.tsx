import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeDynamic, encodeDynamic } from "../../lib/urlState";
import type { DynamicInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { DYNAMIC_PRESETS } from "./presets";
import { DynamicView } from "./DynamicView";
import { EOQ_DEFAULTS, EoqView } from "./EoqView";
import type { EoqInputs } from "./EoqView";

export default function LotSizingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<"dynamic" | "eoq">(
    searchParams.get("mode") === "eoq" ? "eoq" : "dynamic",
  );
  const [inputs, setInputs] = useState<DynamicInputs>(
    () => decodeDynamic("?" + searchParams.toString()) ?? DYNAMIC_PRESETS["Six-period demo"],
  );
  const [eoqInputs, setEoqInputs] = useState<EoqInputs>(EOQ_DEFAULTS);

  const update = (next: DynamicInputs) => {
    setInputs(next);
    setSearchParams(encodeDynamic(next), { replace: true });
  };

  const switchMode = (next: "dynamic" | "eoq") => {
    setMode(next);
    if (next === "eoq") setSearchParams("mode=eoq", { replace: true });
    else setSearchParams(encodeDynamic(inputs), { replace: true });
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button className={mode === "dynamic" ? "active" : ""} onClick={() => switchMode("dynamic")}>
          Dynamic demand
        </button>
        <button className={mode === "eoq" ? "active" : ""} onClick={() => switchMode("eoq")}>
          EOQ
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "dynamic" ? (
          <DynamicView inputs={inputs} onInputs={update} />
        ) : (
          <EoqView inputs={eoqInputs} onInputs={setEoqInputs} />
        )}
      </div>
    </div>
  );
}
