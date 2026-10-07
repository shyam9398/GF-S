import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth, normalizeBisUsername } from "../context/AuthContext";
import {
  Shield,
  Eye,
  EyeOff,
  AlertCircle,
  ArrowLeft,
  Lock,
  HelpCircle,
  X,
  Mail,
} from "lucide-react";

export default function SignIn() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [rawUsername, setRawUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [forgotModalOpen, setForgotModalOpen] = useState(false);

  const [touched, setTouched] = useState({
    username: false,
    password: false,
  });

  // Where to redirect after login (default /dashboard)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const from = (location.state as any)?.from?.pathname || "/dashboard";

  // Handle Username blur: normalize to .bis if entered without suffix
  const handleUsernameBlur = () => {
    setTouched((prev) => ({ ...prev, username: true }));
    if (rawUsername.trim()) {
      setRawUsername(normalizeBisUsername(rawUsername));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    const trimmed = rawUsername.trim();
    if (!trimmed) {
      setFormError("Username is required.");
      setTouched((prev) => ({ ...prev, username: true }));
      return;
    }

    const normalized = normalizeBisUsername(trimmed);
    if (!password) {
      setFormError("Password is required.");
      setTouched((prev) => ({ ...prev, password: true }));
      return;
    }

    try {
      setLoading(true);
      const res = await signIn(normalized, password);
      if (!res.success) {
        setFormError(res.error || "Invalid username or password. Please verify your officer credentials.");
        return;
      }

      // Successful login -> redirect to dashboard
      navigate(from, { replace: true });
    } catch (err: unknown) {
      console.error("SignIn error:", err);
      setFormError("Authentication service unavailable. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans selection:bg-blue-100">
      {/* Top Banner */}
      <div className="border-b border-slate-200 bg-white py-2 px-4 sm:px-6">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link
            to="/procurement-officer"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-[#0F2B48] transition"
          >
            <ArrowLeft size={14} />
            <span>← Back to Officer Entry</span>
          </Link>
          <span className="text-[11px] font-medium text-slate-500 hidden sm:inline">
            Bureau of Indian Standards • Secure Login
          </span>
        </div>
      </div>

      {/* Main Container */}
      <div className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md bg-white border border-slate-200 rounded-2xl shadow-xs p-6 sm:p-8">
          {/* Header */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#0F2B48] text-white shadow-xs border border-blue-950 mb-3">
              <Shield size={24} className="text-red-400" />
            </div>
            <h1 className="text-2xl font-black text-[#0F2B48] tracking-tight">
              Procurement Officer Sign In
            </h1>
            <p className="text-xs text-slate-500 mt-1.5">
              Access the BIS Standards Recommendation Dashboard.
            </p>
          </div>

          {/* Error Notification */}
          {formError && (
            <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-700">
              <AlertCircle size={16} className="shrink-0 mt-0.5 text-red-600" />
              <span>{formError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Username Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="signin-username"
                  className="text-xs font-bold text-slate-700 uppercase tracking-wider"
                >
                  Username
                </label>
                <span className="text-[11px] text-slate-500 font-mono">
                  e.g. officer01.bis
                </span>
              </div>
              <input
                id="signin-username"
                type="text"
                value={rawUsername}
                onChange={(e) => {
                  setRawUsername(e.target.value);
                  if (formError) setFormError(null);
                }}
                onBlur={handleUsernameBlur}
                placeholder="officer01.bis"
                autoComplete="username"
                className={`w-full px-3.5 py-2.5 text-sm rounded-lg border bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition font-mono ${
                  touched.username && !rawUsername.trim()
                    ? "border-red-300 focus:ring-red-400/20 focus:border-red-500"
                    : "border-slate-300 focus:ring-blue-600/20 focus:border-blue-600"
                }`}
              />
              {touched.username && !rawUsername.trim() && (
                <p className="mt-1 text-[11px] text-red-600">
                  Username is required.
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="signin-password"
                  className="text-xs font-bold text-slate-700 uppercase tracking-wider"
                >
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setForgotModalOpen(true)}
                  className="text-[11px] font-semibold text-blue-700 hover:text-blue-900 transition"
                >
                  Forgot Password?
                </button>
              </div>
              <div className="relative">
                <input
                  id="signin-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (formError) setFormError(null);
                  }}
                  onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  className={`w-full px-3.5 py-2.5 pr-10 text-sm rounded-lg border bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition ${
                    touched.password && !password
                      ? "border-red-300 focus:ring-red-400/20 focus:border-red-500"
                      : "border-slate-300 focus:ring-blue-600/20 focus:border-blue-600"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                  tabIndex={-1}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {touched.password && !password && (
                <p className="mt-1 text-[11px] text-red-600">
                  Password is required.
                </p>
              )}
            </div>

            {/* Submit Button */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 px-4 bg-[#0F2B48] hover:bg-[#163c63] text-white text-sm font-bold rounded-lg transition shadow-xs border border-[#0A1F33] flex items-center justify-center gap-2 disabled:opacity-60 cursor-pointer disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Signing In...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </div>
          </form>

          {/* Alternative Links */}
          <div className="mt-6 pt-5 border-t border-slate-200 text-center space-y-2">
            <p className="text-xs text-slate-600">
              Need an officer account?{" "}
              <Link
                to="/signup"
                className="font-bold text-blue-700 hover:text-blue-900 transition"
              >
                Create Account
              </Link>
            </p>
            <div>
              <Link
                to="/"
                className="text-xs font-medium text-slate-500 hover:text-slate-800 transition"
              >
                ← Back to Home
              </Link>
            </div>
          </div>

          {/* Security Note */}
          <div className="mt-4 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
            <Lock size={12} />
            <span>Official Government Access • Supabase Authentication</span>
          </div>
        </div>
      </div>

      {/* Forgot Password Helper Modal */}
      {forgotModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
          <div className="w-full max-w-md bg-white rounded-xl border border-slate-200 p-6 shadow-lg">
            <div className="flex items-start justify-between pb-3 border-b border-slate-200">
              <div className="flex items-center gap-2 text-[#0F2B48]">
                <HelpCircle size={20} className="text-blue-600" />
                <h3 className="text-sm font-bold">Officer Credential Recovery</h3>
              </div>
              <button
                onClick={() => setForgotModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X size={18} />
              </button>
            </div>

            <div className="py-4 space-y-3 text-xs text-slate-600 leading-relaxed">
              <p>
                In accordance with BIS and public procurement security protocols, password resets for official <code className="font-mono text-slate-800 bg-slate-100 px-1 py-0.5 rounded">.bis</code> accounts must be initiated through the authorized Departmental IT Administrator.
              </p>
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-blue-900 space-y-1">
                <p className="font-semibold flex items-center gap-1.5">
                  <Mail size={13} />
                  <span>BIS Helpdesk & Technical Support</span>
                </p>
                <p className="text-[11px] text-blue-800">
                  Email: <span className="font-mono">support@bis.gov.in</span> | Ext: <span className="font-mono">BIS-SEC-26108</span>
                </p>
              </div>
              <p className="text-[11px] text-slate-500">
                If you created this account during local evaluation, you can also register a new <code className="font-mono">.bis</code> officer account via the Create Account page.
              </p>
            </div>

            <div className="pt-3 border-t border-slate-200 flex justify-end">
              <button
                onClick={() => setForgotModalOpen(false)}
                className="px-4 py-2 bg-[#0F2B48] hover:bg-[#163c63] text-white text-xs font-bold rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
