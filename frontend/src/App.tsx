import { Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import Dashboard from "./pages/Dashboard";
import NewAnalysis from "./pages/NewAnalysis";
import AnalysisProgress from "./pages/AnalysisProgress";
import Results from "./pages/Results";
import AnalysisHistory from "./pages/AnalysisHistory";
import Reports from "./pages/Reports";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import LandingPage from "./pages/LandingPage";
import ProcurementOfficerAccess from "./pages/ProcurementOfficerAccess";
import SignIn from "./pages/SignIn";
import SignUp from "./pages/SignUp";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import PublicOnlyRoute from "./components/auth/PublicOnlyRoute";
import { AuthProvider } from "./context/AuthContext";
import { I18nProvider } from "./i18n/I18nContext";

export default function App() {
  return (
    <AuthProvider>
      <I18nProvider>
        <Routes>
          {/* Public Landing & Authentication Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route
            path="/procurement-officer"
            element={
              <PublicOnlyRoute>
                <ProcurementOfficerAccess />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <SignIn />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/signup"
            element={
              <PublicOnlyRoute>
                <SignUp />
              </PublicOnlyRoute>
            }
          />

          {/* Protected Dashboard & Analysis Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <AppShell>
                  <Dashboard />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/new-analysis"
            element={
              <ProtectedRoute>
                <AppShell>
                  <NewAnalysis />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis/new"
            element={
              <ProtectedRoute>
                <AppShell>
                  <NewAnalysis />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis/:id/progress"
            element={
              <ProtectedRoute>
                <AppShell>
                  <AnalysisProgress />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/analysis/:id/results"
            element={
              <ProtectedRoute>
                <AppShell>
                  <Results />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/results/:id"
            element={
              <ProtectedRoute>
                <AppShell>
                  <Results />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <AppShell>
                  <AnalysisHistory />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <AppShell>
                  <Reports />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <AppShell>
                  <Settings />
                </AppShell>
              </ProtectedRoute>
            }
          />

          {/* Fallback 404 Route */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </I18nProvider>
    </AuthProvider>
  );
}