import { Route, Routes } from "react-router-dom";
import { Rail } from "./components/Rail";
import CellularPage from "./pages/cellular/CellularPage";
import Home from "./pages/Home";
import LineBalancingPage from "./pages/line-balancing/LineBalancingPage";
import LotSizingPage from "./pages/lot-sizing/LotSizingPage";
import ProcessAnalysisPage from "./pages/process-analysis/ProcessAnalysisPage";
import ProductivityPage from "./pages/productivity/ProductivityPage";
import SchedulingPage from "./pages/scheduling/SchedulingPage";

export default function App() {
  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Rail />
      <main style={{ flex: 1, minWidth: 0 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/cellular" element={<CellularPage />} />
          <Route path="/line-balancing" element={<LineBalancingPage />} />
          <Route path="/lot-sizing" element={<LotSizingPage />} />
          <Route path="/process-analysis" element={<ProcessAnalysisPage />} />
          <Route path="/productivity" element={<ProductivityPage />} />
          <Route path="/scheduling" element={<SchedulingPage />} />
        </Routes>
      </main>
    </div>
  );
}
