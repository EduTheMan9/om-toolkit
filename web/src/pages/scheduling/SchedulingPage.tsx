import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeDispatch, encodeDispatch } from "../../lib/urlState";
import type { DispatchJob } from "../../lib/urlState";
import "../../components/workbench.css";
import { DISPATCH_PRESETS } from "./presets";
import { DispatchView } from "./DispatchView";

export default function SchedulingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState<DispatchJob[]>(
    () => decodeDispatch("?" + searchParams.toString()) ?? DISPATCH_PRESETS["Five-job demo"],
  );

  const update = (next: DispatchJob[]) => {
    setJobs(next);
    setSearchParams(encodeDispatch(next), { replace: true });
  };

  return (
    <div className="workbench">
      <DispatchView jobs={jobs} onJobs={update} />
    </div>
  );
}
