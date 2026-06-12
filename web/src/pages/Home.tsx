import { Link } from "react-router-dom";
import { MODULES } from "../modules";
import "./Home.css";

export default function Home() {
  return (
    <div className="home">
      <h1>OM Toolkit</h1>
      <p className="subtitle tagline">
        Interactive solvers for the core Operations Management methods — each
        one shows its work, step by step.
      </p>
      <div className="home-grid">
        {MODULES.map((m) => (
          <div key={m.path} className="card module-card">
            <h3>
              <m.icon size={17} color="var(--accent)" /> {m.name}
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
    </div>
  );
}
