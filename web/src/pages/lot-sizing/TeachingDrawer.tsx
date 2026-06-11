import { useEffect, useState } from "react";
import type { SilverMealStep } from "../../lib/api";
import { formatMoney } from "../../lib/format";
import "./TeachingDrawer.css";

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
  const [open, setOpen] = useState(false);
  const [index, setIndex] = useState(0);

  useEffect(() => setIndex(0), [steps]); // new data -> restart the story

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") setIndex((i) => Math.min(i + 1, steps.length - 1));
      if (e.key === "ArrowLeft") setIndex((i) => Math.max(i - 1, 0));
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, steps.length]);

  if (!open) {
    return (
      <button className="drawer-trigger" onClick={() => setOpen(true)}>
        <span>
          💡 <b>Why these lots?</b>{" "}
          <span className="subtitle">
            watch Silver–Meal decide, step by step, on this exact data
          </span>
        </span>
        <span className="go">Walk me through it ▶</span>
      </button>
    );
  }

  const step = steps[Math.min(index, steps.length - 1)];
  return (
    <div className="step-player">
      <div className="label">LEARN · Silver–Meal, narrated by the solver</div>
      <div className="step-card">{describe(step)}</div>
      <div className="step-nav">
        <button onClick={() => setIndex((i) => Math.max(i - 1, 0))} disabled={index === 0}>
          ◀ Back
        </button>
        <button
          className="primary"
          onClick={() => setIndex((i) => Math.min(i + 1, steps.length - 1))}
          disabled={index === steps.length - 1}
        >
          Next ▶
        </button>
        <button onClick={() => setOpen(false)}>Close</button>
        <span className="count">
          step {index + 1} / {steps.length} · arrow keys work too
        </span>
      </div>
    </div>
  );
}
