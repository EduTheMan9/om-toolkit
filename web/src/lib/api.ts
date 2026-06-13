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
  backlog_cost: number;
  total_cost: number;
  ending_inventory: number[];
}

// the three base plans are always returned; the backlog-aware plan only when a
// backlog penalty is supplied
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
  plans: Record<PlanName, PlanResult> & { wagner_whitin_backlog?: PlanResult };
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
  | "wspt"
  | "edd"
  | "lpt"
  | "moore_hodgson"
  | "min_total_tardiness";

export interface DispatchMethodResult {
  sequence: string[];
  schedule: ScheduledJob[];
  avg_completion_time: number;
  weighted_completion_time: number;
  avg_tardiness: number;
  total_tardiness: number;
  max_tardiness: number;
  max_lateness: number;
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

export interface ProductMixAllocation {
  name: string;
  ratio: number;
  units: number;
  minutes: number;
  contribution: number;
  limited_by: "demand" | "capacity";
}

export interface ProductMixStep {
  kind: "rank" | "allocate" | "total";
  order?: string[];
  ratios?: Record<string, number>;
  product?: string;
  ratio?: number;
  units?: number;
  minutes?: number;
  contribution?: number;
  remaining?: number;
  limited_by?: "demand" | "capacity";
  total_contribution?: number;
  idle_minutes?: number;
}

export interface ProductMixResponse {
  allocations: ProductMixAllocation[];
  total_contribution: number;
  used_minutes: number;
  idle_minutes: number;
  available_minutes: number;
  steps: ProductMixStep[];
}

export type LittlesVariable = "inventory" | "flow_rate" | "flow_time";

export interface ProductivityFactor {
  name: string;
  previous: number | null;
  current: number | null;
  change: number | null;
}

export interface ProductivityStep {
  kind: "totals" | "change" | "factor";
  period?: "previous" | "current";
  output?: number;
  total?: number;
  mfp?: number;
  previous?: number | null;
  current?: number | null;
  change?: number | null;
  name?: string;
}

export interface ProductivityResponse {
  multifactor: { previous: number; current: number; change: number };
  factors: ProductivityFactor[];
  steps: ProductivityStep[];
}

export interface OeeStep {
  kind: "availability" | "performance" | "quality" | "oee";
  value: number;
  planned_time?: number;
  downtime?: number;
  run_time?: number;
  ideal_cycle_time?: number;
  total_count?: number;
  good_count?: number;
  availability?: number;
  performance?: number;
  quality?: number;
}

export interface OeeResponse {
  run_time: number;
  availability: number;
  performance: number;
  quality: number;
  oee: number;
  steps: OeeStep[];
}

export interface CellularStep {
  kind: "rows" | "cols" | "converged" | "cells" | "efficacy";
  iteration?: number;
  values?: number[];
  order?: number[];
  changed?: boolean;
  iterations?: number;
  machine_cells?: number[];
  part_cells?: number[];
  n_cells?: number;
  total_ones?: number;
  exceptional?: number;
  voids?: number;
  grouping_efficacy?: number;
}

export interface CellularResponse {
  matrix: number[][]; // echoed input; all orders index into this
  row_order: number[];
  col_order: number[];
  iterations: number;
  machine_cells: number[];
  part_cells: number[];
  n_cells: number;
  total_ones: number;
  exceptional: number;
  voids: number;
  grouping_efficacy: number;
  steps: CellularStep[];
}

export interface LittlesLawResponse {
  solved_for: LittlesVariable;
  inventory: number;
  flow_rate: number;
  flow_time: number;
}

export interface QueueingResponse {
  vut: {
    rho: number;
    V: number;
    U: number;
    T: number;
    Wq: number;
    W: number;
    Lq: number;
    L: number;
  };
  exact: {
    model: "M/M/1" | "M/M/c";
    rho: number;
    Lq: number;
    L: number;
    Wq: number;
    W: number;
    prob_wait: number;
    is_exact_for_inputs: boolean;
  };
  curve: { rho: number[]; wq: number[]; lq: number[] };
}
