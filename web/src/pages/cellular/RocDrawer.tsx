import type { CellularStep } from "../../lib/api";
import { StepPlayer } from "../../components/StepPlayer";
import { formatNumber } from "../../lib/format";

const machine = (i: number) => `M${i + 1}`;
const part = (j: number) => `P${j + 1}`;

/** "M1 = 18, M3 = 18, M2 = 13, M4 = 12" — values listed in the new order. */
function rankList(order: number[], values: number[], name: (i: number) => string) {
  return order.map((i) => `${name(i)} = ${values[i]}`).join(", ");
}

function members(cells: number[], cell: number, name: (i: number) => string) {
  return cells.flatMap((c, i) => (c === cell ? [name(i)] : [])).join(", ");
}

function describe(step: CellularStep) {
  if (step.kind === "rows" || step.kind === "cols") {
    const isRows = step.kind === "rows";
    return (
      <>
        <b>Pass {step.iteration}</b> — read each{" "}
        {isRows ? "machine row" : "part column"} as a binary number (
        {isRows ? "leftmost part" : "topmost machine"} = biggest bit) and sort
        by decreasing value:{" "}
        {rankList(step.order!, step.values!, isRows ? machine : part)}
        {step.changed ? "." : <> — <b>no change</b>.</>}
      </>
    );
  }
  if (step.kind === "converged") {
    return (
      <>
        A full pass changed nothing, so ROC stops after{" "}
        <b>
          {step.iterations} pass{step.iterations! > 1 ? "es" : ""}
        </b>{" "}
        — the 1s have gathered into blocks along the diagonal.
      </>
    );
  }
  if (step.kind === "cells") {
    return (
      <>
        ROC only reorders — the boundaries come from scoring every consecutive
        split of the machine list. Best: <b>{step.n_cells} cells</b>:{" "}
        {Array.from({ length: step.n_cells! }, (_, c) => (
          <span key={c}>
            Cell {c + 1} = {members(step.machine_cells!, c, machine)} ×{" "}
            {members(step.part_cells!, c, part)}
            {c < step.n_cells! - 1 ? " · " : ""}
          </span>
        ))}
        . Each part joins the cell where it has the most operations.
      </>
    );
  }
  return (
    <>
      Grouping efficacy μ = (e − exceptional) / (e + voids) = ({step.total_ones}{" "}
      − <span className="step-bad">{step.exceptional}</span>) / ({step.total_ones}{" "}
      + {step.voids}) = <b>{formatNumber(step.grouping_efficacy!)}</b>.
      Exceptional elements are 1s outside every cell (parts travelling between
      cells); voids are 0s inside a cell (idle pairings). μ = 1 is a perfect
      block diagonal.
    </>
  );
}

export function RocDrawer({ steps }: { steps: CellularStep[] }) {
  return (
    <StepPlayer
      steps={steps}
      title="LEARN · Rank Order Clustering, narrated by the solver"
      question="How did the blocks appear?"
      teaser="watch rows and columns sort by binary value until the cells emerge"
      describe={describe}
    />
  );
}
