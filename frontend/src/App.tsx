import { Navigate, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { ScanDetailPage } from "./pages/ScanDetailPage";
import { TargetDetailPage } from "./pages/TargetDetailPage";
import { TargetsPage } from "./pages/TargetsPage";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Navigate to="/targets" replace />} />
        <Route path="targets" element={<TargetsPage />} />
        <Route path="targets/:id" element={<TargetDetailPage />} />
        <Route path="scans/:id" element={<ScanDetailPage />} />
      </Route>
    </Routes>
  );
}
