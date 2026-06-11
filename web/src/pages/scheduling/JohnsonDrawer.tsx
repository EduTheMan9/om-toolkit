import type { JohnsonStep } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { StepPlayer } from "../../components/StepPlayer";

function describe(step: JohnsonStep) {
  if (step.kind === "done") {
    return (
      <>
        <b>Sequence fixed:</b> {step.sequence!.join(" → ")}. Every pick was
        forced by one rule — smallest remaining time decides — and the result
        is provably the minimal makespan.
      </>
    );
  }
  const front = step.placement === "front";
  return (
    <>
      The smallest processing time left anywhere is <b>{step.job}</b>:{" "}
      <span className="mono">{formatNumber(step.time!)}</span> on machine {step.machine}.{" "}
      {front ? (
        <span className="step-good">
          Short machine-1 work reaches machine 2 quickly — place it as early
          as possible: slot {step.slot}.
        </span>
      ) : (
        <span className="step-bad">
          Short machine-2 work would leave machine 2 idle at the end — push it
          as late as possible: slot {step.slot}.
        </span>
      )}
    </>
  );
}

export function JohnsonDrawer({ steps }: { steps: JohnsonStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Johnson's rule, narrated by the solver"
      question="Why this order?"
      teaser="watch Johnson's rule pick the sequence, job by job, on this exact data"
      describe={describe}
    />
  );
}
