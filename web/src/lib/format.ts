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

/** A fraction in [0, 1] as a percentage, e.g. 0.8095 -> "81.0%". */
export function formatPercent(fraction: number): string {
  return (fraction * 100).toFixed(1) + "%";
}
