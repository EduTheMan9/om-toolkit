import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { decodeDynamic, encodeDynamic } from "../../lib/urlState";
import type { DynamicInputs } from "../../lib/urlState";
import "../../components/workbench.css";
import { DYNAMIC_PRESETS } from "./presets";
import { DynamicView } from "./DynamicView";

export default function LotSizingPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [inputs, setInputs] = useState<DynamicInputs>(
    () => decodeDynamic("?" + searchParams.toString()) ?? DYNAMIC_PRESETS["Six-period demo"],
  );

  const update = (next: DynamicInputs) => {
    setInputs(next);
    setSearchParams(encodeDynamic(next), { replace: true });
  };

  return (
    <div className="workbench">
      <DynamicView inputs={inputs} onInputs={update} />
    </div>
  );
}
