import { Link } from "react-router-dom";
import { MODULES } from "../modules";
import "./Home.css";

export default function Home() {
  return (
    <div className="home">
      <header className="home-hero">
        <h1>OM Toolkit</h1>
        <p className="subtitle tagline">
          Interactive solvers for the core Operations Management methods — each
          one shows its work, step by step.
        </p>
      </header>

      <div className="home-grid">
        {MODULES.map((m) => (
          <div key={m.path} className="card module-card">
            <h3>
              <m.icon size={18} color="var(--accent)" /> {m.name}
            </h3>
            <div className="decision">{m.decision}</div>
            <div className="actions">
              {m.ready ? (
                <>
                  <Link className="open" to={m.path}>
                    Open
                  </Link>
                  {m.exampleSearch && (
                    <Link className="example" to={m.path + m.exampleSearch}>
                      load an example →
                    </Link>
                  )}
                </>
              ) : (
                <span className="soon">Coming soon</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <section className="home-about">
        <h2>How it works</h2>
        <div className="about-grid">
          <div className="about-item">
            <h4>Shows its work</h4>
            <p>
              Every module narrates its algorithm one step at a time — not just
              the answer, but the reasoning behind each pick, so you can follow
              (and explain) exactly how the method arrives at its result.
            </p>
          </div>
          <div className="about-item">
            <h4>Validated by hand</h4>
            <p>
              Each solver is traced through a worked example by hand before its
              test is written, so the numbers you see match how the method is
              taught in an Operations Management course.
            </p>
          </div>
          <div className="about-item">
            <h4>Clean architecture</h4>
            <p>
              The algorithms live in pure Python with zero UI dependencies, a
              thin FastAPI layer exposes them as JSON, and a React frontend
              renders the inputs, charts, and step-by-step explanations.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
