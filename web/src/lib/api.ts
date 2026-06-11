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
