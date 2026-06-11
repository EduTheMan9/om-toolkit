import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  decodeDispatch,
  decodeJohnson,
  encodeDispatch,
  encodeJohnson,
} from "../../lib/urlState";
import type { DispatchJob, JohnsonJob } from "../../lib/urlState";
import "../../components/workbench.css";
import { DISPATCH_PRESETS, JOHNSON_PRESETS } from "./presets";
import { DispatchView } from "./DispatchView";
import { JohnsonView } from "./JohnsonView";

export default function SchedulingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const startJohnson = searchParams.get("mode") === "johnson";
  const initialSearch = "?" + searchParams.toString();

  const [mode, setMode] = useState<"dispatch" | "johnson">(
    startJohnson ? "johnson" : "dispatch",
  );
  const [jobs, setJobs] = useState<DispatchJob[]>(
    () =>
      (startJohnson ? null : decodeDispatch(initialSearch)) ??
      DISPATCH_PRESETS["Five-job demo"],
  );
  const [johnsonJobs, setJohnsonJobs] = useState<JohnsonJob[]>(
    () =>
      (startJohnson ? decodeJohnson(initialSearch) : null) ??
      JOHNSON_PRESETS["Five-job flow shop"],
  );

  const updateDispatch = (next: DispatchJob[]) => {
    setJobs(next);
    setSearchParams(encodeDispatch(next), { replace: true });
  };

  const updateJohnson = (next: JohnsonJob[]) => {
    setJohnsonJobs(next);
    setSearchParams("mode=johnson&" + encodeJohnson(next), { replace: true });
  };

  const switchMode = (next: "dispatch" | "johnson") => {
    setMode(next);
    setSearchParams(
      next === "johnson" ? "mode=johnson&" + encodeJohnson(johnsonJobs) : encodeDispatch(jobs),
      { replace: true },
    );
  };

  return (
    <div className="workbench" style={{ flexDirection: "column" }}>
      <div className="mode-pills" style={{ padding: "14px 18px 0" }}>
        <button
          className={mode === "dispatch" ? "active" : ""}
          onClick={() => switchMode("dispatch")}
        >
          Single machine
        </button>
        <button
          className={mode === "johnson" ? "active" : ""}
          onClick={() => switchMode("johnson")}
        >
          Two-machine flow shop
        </button>
      </div>
      <div style={{ display: "flex", flex: 1 }}>
        {mode === "dispatch" ? (
          <DispatchView jobs={jobs} onJobs={updateDispatch} />
        ) : (
          <JohnsonView jobs={johnsonJobs} onJobs={updateJohnson} />
        )}
      </div>
    </div>
  );
}
