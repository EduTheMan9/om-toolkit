import type { ProductMixStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatMoney, formatNumber } from "../../lib/format";

function describe(step: ProductMixStep) {
  if (step.kind === "rank") {
    return (
      <>
        Rank by <b>contribution per bottleneck-minute</b> ($/min):{" "}
        {step.order!
          .map((name) => `${name} (${formatNumber(step.ratios![name])})`)
          .join(" ▸ ")}
        . The scarce minute is what we are really selling, so the best product
        is the one that earns the most per minute — not per unit.
      </>
    );
  }
  if (step.kind === "allocate") {
    const capped = step.limited_by === "capacity";
    return (
      <>
        <b>{step.product}</b> at {formatNumber(step.ratio!)} $/min: make{" "}
        <b>{formatNumber(step.units!)}</b> units ({formatNumber(step.minutes!)}{" "}
        min) for {formatMoney(step.contribution!)}.{" "}
        {capped ? (
          <span className="step-bad">
            ran out of bottleneck time — only {formatNumber(step.remaining!)} min left
          </span>
        ) : (
          <>met all its demand; {formatNumber(step.remaining!)} min still free</>
        )}
        .
      </>
    );
  }
  return (
    <>
      Total contribution <b>{formatMoney(step.total_contribution!)}</b>, with{" "}
      {formatNumber(step.idle_minutes!)} bottleneck minutes idle. Note the
      highest unit-margin product can end up made last — margin per unit lies
      when a minute, not a unit, is the thing in short supply.
    </>
  );
}

export function ProductMixDrawer({ steps }: { steps: ProductMixStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Product mix, narrated by the solver"
      question="Which product earns the most per scarce minute?"
      teaser="watch the ranking, then the bottleneck minutes get filled in order"
      describe={describe}
    />
  );
}
