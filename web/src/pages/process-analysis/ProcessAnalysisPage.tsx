import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeProcess, encodeProcess } from "../../lib/urlState";
import type { ProcessInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { PROCESS_PRESETS } from "./presets";
import { ProcessView } from "./ProcessView";
import { LITTLES_DEFAULTS, LittlesView } from "./LittlesView";
import type { LittlesInputs } from "./LittlesView";
import { PRODUCT_MIX_DEFAULTS, ProductMixView } from "./ProductMixView";
import type { ProductMixInputs } from "./ProductMixView";
import { QUEUEING_DEFAULTS, QueueingView } from "./QueueingView";
import type { QueueingInputs } from "./QueueingView";

type Mode = "capacity" | "littles" | "mix" | "queue";

export default function ProcessAnalysisPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [mode, setMode] = useState<Mode>(() => {
    const m = searchParams.get("mode");
    return m === "littles" || m === "mix" || m === "queue" ? m : "capacity";
  });
  const [inputs, setInputs] = useState<ProcessInputs>(
    () =>
      decodeProcess("?" + searchParams.toString()) ??
      PROCESS_PRESETS["Sandwich line"],
  );
  const [littles, setLittles] = useState<LittlesInputs>(LITTLES_DEFAULTS);
  const [mix, setMix] = useState<ProductMixInputs>(PRODUCT_MIX_DEFAULTS);
  const [queue, setQueue] = useState<QueueingInputs>(QUEUEING_DEFAULTS);

  const update = (next: ProcessInputs) => {
    setInputs(next);
    setSearchParams(encodeProcess(next), { replace: true });
  };

  const switchMode = (next: Mode) => {
    setMode(next);
    setSearchParams(next === "capacity" ? encodeProcess(inputs) : `mode=${next}`, {
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
        <button
          className={mode === "mix" ? "active" : ""}
          onClick={() => switchMode("mix")}
        >
          Product mix (TOC)
        </button>
        <button
          className={mode === "queue" ? "active" : ""}
          onClick={() => switchMode("queue")}
        >
          Queueing (VUT)
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "capacity" && <ProcessView inputs={inputs} onInputs={update} />}
        {mode === "littles" && <LittlesView inputs={littles} onInputs={setLittles} />}
        {mode === "mix" && <ProductMixView inputs={mix} onInputs={setMix} />}
        {mode === "queue" && <QueueingView inputs={queue} onInputs={setQueue} />}
      </div>
    </div>
  );
}
