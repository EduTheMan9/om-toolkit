import type { OeeStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatNumber, formatPercent } from "../../lib/format";

function describe(step: OeeStep) {
  if (step.kind === "availability") {
    return (
      <>
        <b>Availability</b> = run time ÷ planned time ={" "}
        {formatNumber(step.run_time!)} ÷ {formatNumber(step.planned_time!)} ={" "}
        <b>{formatPercent(step.value)}</b>. We lost {formatNumber(step.downtime!)} min
        to stops, so only that share of the plan was actually running.
      </>
    );
  }
  if (step.kind === "performance") {
    return (
      <>
        <b>Performance</b> = ideal cycle × total ÷ run time ={" "}
        {formatNumber(step.ideal_cycle_time!)} × {formatNumber(step.total_count!)} ÷{" "}
        {formatNumber(step.run_time!)} = <b>{formatPercent(step.value)}</b>. This
        is how fast we actually ran versus the ideal pace — the speed loss,
        independent of whether the units were any good.
      </>
    );
  }
  if (step.kind === "quality") {
    return (
      <>
        <b>Quality</b> = good ÷ total = {formatNumber(step.good_count!)} ÷{" "}
        {formatNumber(step.total_count!)} = <b>{formatPercent(step.value)}</b>.
        The defect loss — units made, but not made right.
      </>
    );
  }
  return (
    <>
      <b>OEE</b> = {formatPercent(step.availability!)} ×{" "}
      {formatPercent(step.performance!)} × {formatPercent(step.quality!)} ={" "}
      <b>{formatPercent(step.value)}</b>. The three multiply because they are
      independent losses on the same planned time: a stop, a slowdown, and a
      scrap each chip away at a different slice.
    </>
  );
}

export function OeeDrawer({ steps }: { steps: OeeStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · OEE, narrated by the solver"
      question="Where did the planned time go?"
      teaser="watch each loss — stops, speed, scrap — peel off one factor at a time"
      describe={describe}
    />
  );
}
