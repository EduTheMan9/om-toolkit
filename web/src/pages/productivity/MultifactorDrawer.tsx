import type { ProductivityStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatMoney, formatNumber } from "../../lib/format";
import { formatChange } from "./charts";

function describe(step: ProductivityStep) {
  if (step.kind === "totals") {
    return (
      <>
        <b>{step.period === "previous" ? "Last period" : "This period"}</b>:
        output {formatMoney(step.output!)} ÷ total input cost{" "}
        {formatMoney(step.total!)} = <b>{formatNumber(step.mfp!)}</b> $ of
        output per $ of input. Inputs can only be added because they share a
        unit — money.
      </>
    );
  }
  if (step.kind === "change") {
    const good = step.change! >= 0;
    return (
      <>
        Multifactor productivity went {formatNumber(step.previous!)} →{" "}
        {formatNumber(step.current!)}:{" "}
        <span className={good ? "step-good" : "step-bad"}>
          {formatChange(step.change!)}
        </span>
        . This is the honest aggregate — it divides by ALL the inputs
        together, so nothing can hide.
      </>
    );
  }
  if (step.previous == null) {
    return (
      <>
        <b>{step.name}</b> has zero cost in one of the periods — output per $
        of it is undefined, so it shows as "—".
      </>
    );
  }
  return (
    <>
      <b>{step.name}</b> alone: {formatNumber(step.previous!)} →{" "}
      {formatNumber(step.current!)} (
      <span className={step.change! >= 0 ? "step-good" : "step-bad"}>
        {formatChange(step.change!)}
      </span>
      ) — single-factor ratios divide by ONE input, so a factor can look
      great while the others absorb the load.
    </>
  );
}

export function MultifactorDrawer({ steps }: { steps: ProductivityStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Multifactor productivity, narrated by the solver"
      question="Did we actually get more productive?"
      teaser="watch each period's ratio get computed, then each factor's side of the story"
      describe={describe}
    />
  );
}
