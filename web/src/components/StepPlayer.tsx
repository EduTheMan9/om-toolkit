import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import "./StepPlayer.css";

/** "Algorithms that narrate themselves": a collapsed teaser button that
 * opens a dark step-by-step player over structured solver steps
 * (◀ ▶ buttons + keyboard arrows). Each module supplies its own describe(). */
export function StepPlayer<T>({
  steps,
  title,
  question,
  teaser,
  describe,
}: {
  steps: T[];
  title: string;
  question: string;
  teaser: string;
  describe: (step: T) => ReactNode;
}) {
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
          💡 <b>{question}</b> <span className="subtitle">{teaser}</span>
        </span>
        <span className="go">Walk me through it ▶</span>
      </button>
    );
  }

  const step = steps[Math.min(index, steps.length - 1)];
  return (
    <div className="step-player">
      <div className="label">{title}</div>
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
