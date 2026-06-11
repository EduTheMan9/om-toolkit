import type { RpwStep } from "../../lib/api";
import { formatNumber } from "../../lib/format";
import { StepPlayer } from "../../components/StepPlayer";

function describe(step: RpwStep) {
  if (step.kind === "rank") {
    return (
      <>
        <b>Rank by positional weight</b> — each task's own time plus everything
        downstream of it:{" "}
        <span className="mono">
          {step.order!.map((id) => `${id} (${formatNumber(step.weights![id])})`).join(" → ")}
        </span>
        . Heavy weights head long chains of work, so they go first.
      </>
    );
  }
  if (step.kind === "assign") {
    return (
      <>
        <b>{step.task}</b> is the highest-ranked task that is unblocked and
        fits — assign it to station {step.station}.{" "}
        <span className="step-good">
          {formatNumber(step.remaining!)} time left in the station.
        </span>
      </>
    );
  }
  if (step.kind === "skip") {
    if (step.reason === "blocked") {
      return (
        <>
          <b>{step.task}</b> can't start yet — predecessor
          {step.missing!.length > 1 ? "s" : ""} {step.missing!.join(", ")} not
          assigned. Skip it for now.
        </>
      );
    }
    return (
      <>
        <b>{step.task}</b> is unblocked but needs {formatNumber(step.duration!)}{" "}
        with only {formatNumber(step.remaining!)} left in station {step.station}.{" "}
        <span className="step-bad">Doesn't fit — skip.</span>
      </>
    );
  }
  return (
    <>
      <b>Station {step.station} closes</b> with {step.tasks!.join(", ")}:{" "}
      {formatNumber(step.total!)} used, {formatNumber(step.idle!)} idle.
    </>
  );
}

export function RpwDrawer({ steps }: { steps: RpwStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Ranked Positional Weight, narrated by the solver"
      question="Why these stations?"
      teaser="watch RPW rank the tasks and fill each station, on this exact data"
      describe={describe}
    />
  );
}
