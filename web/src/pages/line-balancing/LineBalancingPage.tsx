import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeBalancing, encodeBalancing } from "../../lib/urlState";
import type { BalancingInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { BALANCING_PRESETS } from "./presets";
import { BalancingView } from "./BalancingView";

export default function LineBalancingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputs, setInputs] = useState<BalancingInputs>(
    () =>
      decodeBalancing("?" + searchParams.toString()) ??
      BALANCING_PRESETS["Six-task demo"],
  );

  const update = (next: BalancingInputs) => {
    setInputs(next);
    setSearchParams(encodeBalancing(next), { replace: true });
  };

  return (
    <div className="workbench">
      <BalancingView inputs={inputs} onInputs={update} />
    </div>
  );
}
