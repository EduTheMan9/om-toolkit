export function formatMoney(value: number): string {
  return "$" + value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}

/** Gap to the best plan, e.g. +41% — what choosing this method costs you. */
export function percentGap(cost: number, best: number): string {
  return `+${Math.round((cost / best - 1) * 100)}%`;
}

export function formatNumber(value: number): string {
  return value.toLocaleString("en-US", { maximumFractionDigits: 2 });
}
