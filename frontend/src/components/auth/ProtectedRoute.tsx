import { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { ShieldCheck } from "lucide-react";

interface ProtectedRouteProps {
  children: ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F8FA] flex flex-col items-center justify-center p-4">
        <div className="w-full max-w-sm bg-white rounded-xl border border-slate-200 p-8 shadow-xs text-center">
          <div className="relative mx-auto w-12 h-12 mb-4 flex items-center justify-center rounded-xl bg-blue-50 text-blue-700 border border-blue-200">
            <ShieldCheck size={28} className="animate-pulse" />
          </div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight">
            BIS Procurement Intelligence
          </h2>
          <p className="text-xs text-slate-500 mt-1 mb-6">
            Verifying Procurement Officer credentials...
          </p>
          <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div className="bg-blue-600 h-1.5 rounded-full w-2/3 animate-[pulse_1.5s_ease-in-out_infinite]" />
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
