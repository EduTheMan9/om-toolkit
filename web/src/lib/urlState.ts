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

export interface DispatchJob {
  id: string;
  processingTime: number;
  dueDate: number;
}

export interface JohnsonJob {
  id: string;
  timeM1: number;
  timeM2: number;
}

// Job lists encode as j=id,num,num;id,num,num — both scheduling modes share
// the shape (id + two numbers). IDs containing "," or ";" would break the
// format; decode returns null and the page falls back to a preset.
function encodeTriples(triples: [string, number, number][]): string {
  const params = new URLSearchParams();
  params.set("j", triples.map((t) => t.join(",")).join(";"));
  return params.toString();
}

function decodeTriples(search: string): [string, number, number][] | null {
  const raw = new URLSearchParams(search).get("j");
  if (!raw) return null;
  const triples: [string, number, number][] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const a = Number(fields[1]);
    const b = Number(fields[2]);
    if (Number.isNaN(a) || Number.isNaN(b)) return null;
    triples.push([fields[0], a, b]);
  }
  return triples;
}

export function encodeDispatch(jobs: DispatchJob[]): string {
  return encodeTriples(jobs.map((j) => [j.id, j.processingTime, j.dueDate]));
}

export function decodeDispatch(search: string): DispatchJob[] | null {
  const triples = decodeTriples(search);
  if (!triples) return null;
  return triples.map(([id, processingTime, dueDate]) => ({ id, processingTime, dueDate }));
}

export function encodeJohnson(jobs: JohnsonJob[]): string {
  return encodeTriples(jobs.map((j) => [j.id, j.timeM1, j.timeM2]));
}

export function decodeJohnson(search: string): JohnsonJob[] | null {
  const triples = decodeTriples(search);
  if (!triples) return null;
  return triples.map(([id, timeM1, timeM2]) => ({ id, timeM1, timeM2 }));
}
