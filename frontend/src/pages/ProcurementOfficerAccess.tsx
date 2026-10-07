import { Link } from "react-router-dom";
import { Shield, LogIn, UserPlus, ArrowLeft, CheckCircle2, Lock } from "lucide-react";

export default function ProcurementOfficerAccess() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans">
      {/* Top Banner */}
      <div className="border-b border-slate-200 bg-white py-2 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-[#0F2B48] transition"
          >
            <ArrowLeft size={14} />
            <span>← Back to Home</span>
          </Link>
          <span className="text-[11px] font-medium text-slate-500 hidden sm:inline">
            Bureau of Indian Standards • Official Portal
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xs p-6 sm:p-8">
          {/* Header Shield */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[#0F2B48] text-white shadow-xs border border-blue-950 mb-4">
              <Shield size={28} className="text-red-400" />
            </div>
            <div className="inline-block px-2.5 py-0.5 mb-2 bg-blue-50 text-blue-900 border border-blue-200 rounded text-[11px] font-bold tracking-wider uppercase">
              Official Portal Entry
            </div>
            <h1 className="text-2xl font-black text-[#0F2B48] tracking-tight">
              Procurement Officer Access
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 mt-2">
              Access the BIS Standards Recommendation Dashboard.
            </p>
          </div>

          {/* Access Info Box */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 mb-6 text-xs text-slate-700 space-y-2">
            <div className="flex items-start gap-2">
              <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
              <span>Dedicated access for Departmental Procurement Officers.</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
              <span>Uses official <code className="px-1 py-0.5 bg-slate-200/80 rounded font-mono text-[11px] text-slate-800">.bis</code> officer identifiers.</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 size={15} className="text-emerald-600 shrink-0 mt-0.5" />
              <span>Automated Indian Standards discovery & compliance audit trails.</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Link
              to="/login"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[#0F2B48] hover:bg-[#163c63] text-white text-sm font-bold rounded-lg transition shadow-xs border border-[#0A1F33]"
            >
              <LogIn size={16} />
              <span>Sign In</span>
            </Link>

            <Link
              to="/signup"
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-white hover:bg-slate-50 text-[#0F2B48] text-sm font-bold rounded-lg transition border border-slate-300 shadow-2xs"
            >
              <UserPlus size={16} />
              <span>Create Account</span>
            </Link>
          </div>

          {/* Back Link */}
          <div className="mt-6 pt-5 border-t border-slate-200 text-center">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
            >
              <span>← Back to Home</span>
            </Link>
          </div>

          {/* Security notice */}
          <div className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
            <Lock size={12} />
            <span>Protected by BIS Role-Based Security & Supabase Auth</span>
          </div>
        </div>
      </div>
    </div>
  );
}
