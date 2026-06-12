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

export interface BalancingTask {
  id: string;
  duration: number;
  predecessors: string[];
}

export interface BalancingInputs {
  tasks: BalancingTask[];
  cycleTime: number | null; // direct mode...
  availableTime: number | null; // ...or demand mode (both null-able, one set)
  demand: number | null;
}

// Tasks encode as t=id,duration,pred.pred;... (predecessors joined by ".").
// Cycle time is ct=10 (direct) or at=480&dm=70 (derived, floored server-side).
export function encodeBalancing(inputs: BalancingInputs): string {
  const params = new URLSearchParams();
  params.set(
    "t",
    inputs.tasks
      .map((t) => [t.id, t.duration, t.predecessors.join(".")].join(","))
      .join(";"),
  );
  if (inputs.cycleTime !== null) {
    params.set("ct", String(inputs.cycleTime));
  } else {
    params.set("at", String(inputs.availableTime));
    params.set("dm", String(inputs.demand));
  }
  return params.toString();
}

export function decodeBalancing(search: string): BalancingInputs | null {
  const params = new URLSearchParams(search);
  const raw = params.get("t");
  if (!raw) return null;
  const tasks: BalancingTask[] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const duration = Number(fields[1]);
    if (Number.isNaN(duration)) return null;
    tasks.push({
      id: fields[0],
      duration,
      predecessors: fields[2] ? fields[2].split(".").filter(Boolean) : [],
    });
  }
  const ct = params.get("ct");
  if (ct !== null) {
    const cycleTime = Number(ct);
    if (Number.isNaN(cycleTime)) return null;
    return { tasks, cycleTime, availableTime: null, demand: null };
  }
  const at = params.get("at");
  const dm = params.get("dm");
  if (at === null || dm === null) return null;
  const availableTime = Number(at);
  const demand = Number(dm);
  if (Number.isNaN(availableTime) || Number.isNaN(demand)) return null;
  return { tasks, cycleTime: null, availableTime, demand };
}

export interface ProcessResourceInput {
  name: string;
  timeMin: number; // minutes per unit (the UI's display unit convention)
  servers: number;
}

export interface ProcessInputs {
  resources: ProcessResourceInput[];
  demandPerHour: number | null; // null = capacity-only analysis
}

// Resources encode as r=name,minutes,servers;... plus optional d=<units/hour>.
// Names containing "," or ";" break the format; decode returns null and the
// page falls back to a preset.
export function encodeProcess(inputs: ProcessInputs): string {
  const params = new URLSearchParams();
  params.set(
    "r",
    inputs.resources
      .map((x) => [x.name, x.timeMin, x.servers].join(","))
      .join(";"),
  );
  if (inputs.demandPerHour !== null) params.set("d", String(inputs.demandPerHour));
  return params.toString();
}

export function decodeProcess(search: string): ProcessInputs | null {
  const params = new URLSearchParams(search);
  const raw = params.get("r");
  if (!raw) return null;
  const resources: ProcessResourceInput[] = [];
  for (const part of raw.split(";")) {
    const fields = part.split(",");
    if (fields.length !== 3 || !fields[0]) return null;
    const timeMin = Number(fields[1]);
    const servers = Number(fields[2]);
    if (Number.isNaN(timeMin) || Number.isNaN(servers)) return null;
    resources.push({ name: fields[0], timeMin, servers });
  }
  const d = params.get("d");
  if (d === null) return { resources, demandPerHour: null };
  const demandPerHour = Number(d);
  if (Number.isNaN(demandPerHour)) return null;
  return { resources, demandPerHour };
}
