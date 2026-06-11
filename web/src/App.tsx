import { Route, Routes } from "react-router-dom";
import { Rail } from "./components/Rail";
import ComingSoon from "./pages/ComingSoon";
import Home from "./pages/Home";
import LotSizingPage from "./pages/lot-sizing/LotSizingPage";
import { MODULES } from "./modules";

export default function App() {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Rail />
      <main style={{ flex: 1, minWidth: 0 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/lot-sizing" element={<LotSizingPage />} />
          {MODULES.filter((m) => !m.ready).map((m) => (
            <Route key={m.path} path={m.path} element={<ComingSoon />} />
          ))}
        </Routes>
      </main>
    </div>
  );
}
