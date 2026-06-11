// Inputs serialize to the query string so a solved problem is a sharable link.
export interface DynamicInputs {
  demands: number[];
  setupCost: number;
  holdingCost: number;
}

export function encodeDynamic(inputs: DynamicInputs): string {
  const params = new URLSearchParams();
  params.set("d", inputs.demands.join(","));
  params.set("s", String(inputs.setupCost));
  params.set("h", String(inputs.holdingCost));
  return params.toString();
}

export function decodeDynamic(search: string): DynamicInputs | null {
  const params = new URLSearchParams(search);
  const d = params.get("d");
  const s = params.get("s");
  const h = params.get("h");
  if (!d || !s || !h) return null;
  const demands = d.split(",").map(Number);
  const setupCost = Number(s);
  const holdingCost = Number(h);
  if (demands.some(Number.isNaN) || Number.isNaN(setupCost) || Number.isNaN(holdingCost)) {
    return null;
  }
  return { demands, setupCost, holdingCost };
}
