import { Hexagon } from "lucide-react";
import { NavLink } from "react-router-dom";
import { MODULES } from "../modules";
import "./Rail.css";

export function Rail() {
  return (
    <nav className="rail">
      <NavLink to="/" className="rail-logo" title="Home" aria-label="Home">
        <Hexagon size={22} />
      </NavLink>
      {MODULES.map((m) => (
        <NavLink
          key={m.path}
          to={m.path}
          title={m.name}
          aria-label={m.name}
          className={({ isActive }) => `rail-item${isActive ? " active" : ""}`}
        >
          <m.icon size={19} />
        </NavLink>
      ))}
    </nav>
  );
}
