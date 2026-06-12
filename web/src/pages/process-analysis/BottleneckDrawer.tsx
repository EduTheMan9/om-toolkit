import type { ProcessStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatNumber } from "../../lib/format";
import { perHour } from "./charts";

function describe(step: ProcessStep) {
  if (step.kind === "capacity") {
    return (
      <>
        <b>{step.resource}</b> takes {formatNumber(step.processing_time!)} min/unit
        with {step.servers} server{step.servers! > 1 ? "s" : ""} → capacity ={" "}
        {step.servers} ÷ {formatNumber(step.processing_time!)} ={" "}
        <b>{perHour(step.capacity!)} units/hour</b>.
      </>
    );
  }
  if (step.kind === "bottleneck") {
    return (
      <>
        The lowest capacity wins: <b>{step.resource}</b> at{" "}
        {perHour(step.capacity!)}/h is the{" "}
        <span className="step-bad">bottleneck</span> — the process can never
        flow faster than its slowest resource.
      </>
    );
  }
  if (step.kind === "flow_rate") {
    if (step.constraint === "demand") {
      return (
        <>
          Demand ({perHour(step.demand!)}/h) is below the bottleneck's{" "}
          {perHour(step.capacity!)}/h, so the process is{" "}
          <span className="step-good">demand-constrained</span>: flow rate ={" "}
          <b>{perHour(step.rate!)}/h</b>.
        </>
      );
    }
    return (
      <>
        {step.demand != null
          ? `Demand (${perHour(step.demand)}/h) exceeds what the bottleneck can do, so the process is `
          : "With no demand given, the process is "}
        <span className="step-bad">capacity-constrained</span>: flow rate =
        bottleneck capacity = <b>{perHour(step.rate!)}/h</b>.
      </>
    );
  }
  return (
    <>
      <b>{step.resource}</b> runs at{" "}
      <b>{Math.round(step.utilization! * 100)}%</b> utilization (flow rate ÷
      its capacity)
      {step.implied != null && step.implied > 1 ? (
        <>
          {" "}— but meeting demand would imply{" "}
          <span className="step-bad">{Math.round(step.implied * 100)}%</span>:
          it is overloaded.
        </>
      ) : (
        "."
      )}
    </>
  );
}

export function BottleneckDrawer({ steps }: { steps: ProcessStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Capacity analysis, narrated by the solver"
      question="Why this bottleneck?"
      teaser="watch each resource's capacity get computed and the slowest one set the pace"
      describe={describe}
    />
  );
}
