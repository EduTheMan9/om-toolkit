import type { SilverMealStep } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import { StepPlayer } from "../../components/StepPlayer";

function describe(step: SilverMealStep) {
  if (step.kind === "open_lot") {
    return (
      <>
        <b>Lot {step.lot}</b> opens with an order in period {step.period}. One
        setup is now committed — every period this lot covers shares it.
      </>
    );
  }
  if (step.kind === "try_extend") {
    const better = step.decision === "extend";
    return (
      <>
        Should lot {step.lot} also cover period {step.period}? Average cost per
        period covered: <span className="mono">{formatMoney(step.avg_current!)}</span> now →{" "}
        <span className="mono">{formatMoney(step.avg_extended!)}</span> if extended.{" "}
        {better ? (
          <span className="step-good">Cheaper per period — extend. ✓</span>
        ) : (
          <span className="step-bad">More expensive per period — stop here. ✕</span>
        )}
      </>
    );
  }
  return (
    <>
      <b>Lot {step.lot} fixed:</b> one order of {step.quantity} units in period{" "}
      {step.start} covers periods {step.start}–{step.end}.
    </>
  );
}

export function TeachingDrawer({ steps }: { steps: SilverMealStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Silver–Meal, narrated by the solver"
      question="Why these lots?"
      teaser="watch Silver–Meal decide, step by step, on this exact data"
      describe={describe}
    />
  );
}
