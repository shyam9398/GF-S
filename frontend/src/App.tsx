import { Navigate, Route, Routes } from "react-router-dom";

import AppShell from "./components/layout/AppShell";

import Dashboard from "./pages/Dashboard";
import NewAnalysis from "./pages/NewAnalysis";
import AnalysisProgress from "./pages/AnalysisProgress";
import Results from "./pages/Results";
import AnalysisHistory from "./pages/AnalysisHistory";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <AppShell>

      <Routes>

        <Route
          path="/"
          element={<Navigate to="/dashboard" replace />}
        />

        <Route
          path="/dashboard"
          element={<Dashboard />}
        />

        <Route
          path="/analysis/new"
          element={<NewAnalysis />}
        />

        <Route
          path="/analysis/:id/progress"
          element={<AnalysisProgress />}
        />

        <Route
          path="/analysis/:id/results"
          element={<Results />}
        />

        <Route
          path="/history"
          element={<AnalysisHistory />}
        />

        <Route
          path="/reports"
          element={<Reports />}
        />

        <Route
          path="/settings"
          element={<Settings />}
        />

        <Route
          path="*"
          element={<NotFound />}
        />

      </Routes>

    </AppShell>
  );
}