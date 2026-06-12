// Typed client for the FastAPI backend. Core's ValueError messages arrive
// as {detail} on 422 and are shown inline next to the inputs.
export class ApiError extends Error {}

export async function postJson<TRes>(path: string, body: unknown): Promise<TRes> {
  const res = await fetch("/api" + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(data?.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export interface PlanResult {
  orders: number[];
  setups: number;
  setup_cost: number;
  holding_cost: number;
  total_cost: number;
  ending_inventory: number[];
}

export type PlanName = "lot_for_lot" | "silver_meal" | "wagner_whitin";

export interface SilverMealStep {
  kind: "open_lot" | "try_extend" | "close_lot";
  lot: number;
  period?: number;
  avg_current?: number;
  avg_extended?: number;
  decision?: "extend" | "stop";
  start?: number;
  end?: number;
  quantity?: number;
}

export interface DynamicResponse {
  plans: Record<PlanName, PlanResult>;
  steps: SilverMealStep[];
}

export interface EoqResponse {
  quantity: number;
  orders_per_period: number;
  time_between_orders: number;
  ordering_cost_total: number;
  holding_cost_total: number;
  total_cost: number;
  curve: { q: number[]; ordering: number[]; holding: number[]; total: number[] };
}

export interface ScheduledJob {
  id: string;
  start: number;
  end: number;
}

export type DispatchMethodName =
  | "fcfs"
  | "spt"
  | "edd"
  | "lpt"
  | "moore_hodgson"
  | "min_total_tardiness";

export interface DispatchMethodResult {
  sequence: string[];
  schedule: ScheduledJob[];
  avg_completion_time: number;
  avg_tardiness: number;
  total_tardiness: number;
  max_tardiness: number;
  num_tardy: number;
}

export interface DispatchResponse {
  // min_total_tardiness is omitted beyond 15 jobs, hence Partial
  methods: Partial<Record<DispatchMethodName, DispatchMethodResult>>;
  optimal_capped: boolean;
}

export interface JohnsonStep {
  kind: "pick" | "done";
  job?: string;
  time?: number;
  machine?: 1 | 2;
  placement?: "front" | "back";
  slot?: number;
  sequence?: string[];
}

export interface JohnsonResponse {
  sequence: string[];
  machine1: ScheduledJob[];
  machine2: ScheduledJob[];
  makespan: number;
  input_order_makespan: number;
  steps: JohnsonStep[];
}

export type HeuristicName = "lcr" | "rpw" | "kilbridge_wester";

export interface BalancingStation {
  index: number;
  task_ids: string[];
  total_time: number;
  idle_time: number;
}

export interface HeuristicResult {
  stations: BalancingStation[];
  num_stations: number;
  efficiency: number;
  balance_delay: number;
  smoothness_index: number;
}

export interface RpwStep {
  kind: "rank" | "assign" | "skip" | "close";
  order?: string[];
  weights?: Record<string, number>;
  station?: number;
  task?: string;
  duration?: number;
  remaining?: number;
  reason?: "blocked" | "no_fit";
  missing?: string[];
  tasks?: string[];
  total?: number;
  idle?: number;
}

export interface BalancingResponse {
  cycle_time: number;
  total_work: number;
  min_stations: number;
  columns: Record<string, number>;
  weights: Record<string, number>;
  heuristics: Record<HeuristicName, HeuristicResult>;
  steps: RpwStep[];
}

export interface ProcessResource {
  name: string;
  processing_time: number;
  servers: number;
  capacity: number;
  utilization: number;
  implied_utilization: number | null;
}

export interface ProcessStep {
  kind: "capacity" | "bottleneck" | "flow_rate" | "utilization";
  resource?: string;
  processing_time?: number;
  servers?: number;
  capacity?: number;
  demand?: number | null;
  rate?: number;
  constraint?: "demand" | "capacity";
  utilization?: number;
  implied?: number | null;
}

export interface ProcessResponse {
  bottleneck: string;
  process_capacity: number;
  flow_rate: number;
  constraint: "demand" | "capacity";
  unloaded_flow_time: number;
  resources: ProcessResource[];
  steps: ProcessStep[];
}

export type LittlesVariable = "inventory" | "flow_rate" | "flow_time";

export interface LittlesLawResponse {
  solved_for: LittlesVariable;
  inventory: number;
  flow_rate: number;
  flow_time: number;
}
