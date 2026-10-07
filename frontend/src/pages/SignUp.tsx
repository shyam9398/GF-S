import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth, normalizeBisUsername, validateBisUsername } from "../context/AuthContext";
import {
  Shield,
  Eye,
  EyeOff,
  UserCheck,
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Lock,
} from "lucide-react";

export default function SignUp() {
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const [rawUsername, setRawUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  // Field touch state for inline validation
  const [touched, setTouched] = useState({
    username: false,
    password: false,
    confirmPassword: false,
  });

  // Real-time normalized username
  const normalizedUsername = rawUsername.trim() ? normalizeBisUsername(rawUsername) : "";

  // Handle Username Change with .bis rule
  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setRawUsername(e.target.value);
    if (formError) setFormError(null);
  };

  // On Username Blur: automatically convert/display [input].bis if not already ending in .bis
  const handleUsernameBlur = () => {
    setTouched((prev) => ({ ...prev, username: true }));
    if (rawUsername.trim()) {
      const formatted = normalizeBisUsername(rawUsername);
      setRawUsername(formatted);
    }
  };

  // Validation calculations
  const usernameValidation = validateBisUsername(rawUsername);
  const isUsernameValid = rawUsername.trim().length > 0 && usernameValidation.isValid;

  const isPasswordLongEnough = password.length >= 8;
  const isPasswordValid = password.length > 0 && isPasswordLongEnough;

  const doPasswordsMatch = password.length > 0 && password === confirmPassword;

  // Handle Form Submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);

    // Auto-normalize on submit as well
    const finalUsername = normalizeBisUsername(rawUsername);
    if (finalUsername !== rawUsername) {
      setRawUsername(finalUsername);
    }

    // Comprehensive validation checks
    if (!rawUsername.trim()) {
      setFormError("Username cannot be empty.");
      setTouched((prev) => ({ ...prev, username: true }));
      return;
    }

    const valResult = validateBisUsername(finalUsername);
    if (!valResult.isValid) {
      setFormError(valResult.error || "Username must end with .bis");
      setTouched((prev) => ({ ...prev, username: true }));
      return;
    }

    if (!password) {
      setFormError("Password cannot be empty.");
      setTouched((prev) => ({ ...prev, password: true }));
      return;
    }

    if (password.length < 8) {
      setFormError("Password must be at least 8 characters.");
      setTouched((prev) => ({ ...prev, password: true }));
      return;
    }

    if (password !== confirmPassword) {
      setFormError("Password and Re-enter Password must match.");
      setTouched((prev) => ({ ...prev, confirmPassword: true }));
      return;
    }

    try {
      setLoading(true);
      const res = await signUp(finalUsername, password);
      if (!res.success) {
        setFormError(res.error || "Account creation failed.");
        return;
      }

      setFormSuccess("Officer account created successfully! Redirecting to dashboard...");
      setTimeout(() => {
        navigate("/dashboard", { replace: true });
      }, 1000);
    } catch (err: unknown) {
      console.error("SignUp error:", err);
      setFormError("An unexpected error occurred while creating your account.");
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
            Bureau of Indian Standards • Official Registration
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
              Create Procurement Officer Account
            </h1>
            <p className="text-xs text-slate-500 mt-1.5">
              Register your official BIS procurement identity for standards discovery.
            </p>
          </div>

          {/* Error / Success Notifications */}
          {formError && (
            <div className="mb-5 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2.5 text-xs text-red-700">
              <AlertCircle size={16} className="shrink-0 mt-0.5 text-red-600" />
              <span>{formError}</span>
            </div>
          )}

          {formSuccess && (
            <div className="mb-5 p-3 rounded-lg bg-emerald-50 border border-emerald-200 flex items-start gap-2.5 text-xs text-emerald-800">
              <CheckCircle2 size={16} className="shrink-0 mt-0.5 text-emerald-600" />
              <span>{formSuccess}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            {/* Username Field */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label
                  htmlFor="signup-username"
                  className="text-xs font-bold text-slate-700 uppercase tracking-wider"
                >
                  Username
                </label>
                <span className="text-[11px] text-blue-800 font-mono font-medium">
                  Rule: Ends with .bis
                </span>
              </div>
              <div className="relative">
                <input
                  id="signup-username"
                  type="text"
                  value={rawUsername}
                  onChange={handleUsernameChange}
                  onBlur={handleUsernameBlur}
                  placeholder="e.g. rajesh or officer01.bis"
                  autoComplete="username"
                  className={`w-full px-3.5 py-2.5 text-sm rounded-lg border bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition font-mono ${
                    touched.username && !isUsernameValid && rawUsername.trim()
                      ? "border-red-300 focus:ring-red-400/20 focus:border-red-500"
                      : "border-slate-300 focus:ring-blue-600/20 focus:border-blue-600"
                  }`}
                />
                {isUsernameValid && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 text-emerald-600">
                    <CheckCircle2 size={16} />
                  </div>
                )}
              </div>

              {/* Real-time converted display preview */}
              {rawUsername.trim() && (
                <div className="mt-1.5 flex items-center gap-1.5 text-[11px] text-slate-500">
                  <UserCheck size={13} className="text-blue-600 shrink-0" />
                  <span>
                    Officer ID:{" "}
                    <strong className="font-mono text-blue-900">
                      {normalizedUsername}
                    </strong>
                  </span>
                </div>
              )}

              {/* Inline validation error */}
              {touched.username && !usernameValidation.isValid && (
                <p className="mt-1 text-[11px] text-red-600">
                  {usernameValidation.error}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div>
              <label
                htmlFor="signup-password"
                className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Password
              </label>
              <div className="relative">
                <input
                  id="signup-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (formError) setFormError(null);
                  }}
                  onBlur={() => setTouched((prev) => ({ ...prev, password: true }))}
                  placeholder="Minimum 8 characters"
                  autoComplete="new-password"
                  className={`w-full px-3.5 py-2.5 pr-10 text-sm rounded-lg border bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition ${
                    touched.password && !isPasswordValid
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

              {/* Inline validation */}
              {touched.password && !isPasswordLongEnough && (
                <p className="mt-1 text-[11px] text-red-600">
                  Password must be at least 8 characters.
                </p>
              )}
            </div>

            {/* Re-enter Password Field */}
            <div>
              <label
                htmlFor="signup-confirm-password"
                className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5"
              >
                Re-enter Password
              </label>
              <div className="relative">
                <input
                  id="signup-confirm-password"
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => {
                    setConfirmPassword(e.target.value);
                    if (formError) setFormError(null);
                  }}
                  onBlur={() => setTouched((prev) => ({ ...prev, confirmPassword: true }))}
                  placeholder="Re-enter your password"
                  autoComplete="new-password"
                  className={`w-full px-3.5 py-2.5 pr-10 text-sm rounded-lg border bg-white text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 transition ${
                    touched.confirmPassword && (!doPasswordsMatch || !confirmPassword)
                      ? "border-red-300 focus:ring-red-400/20 focus:border-red-500"
                      : "border-slate-300 focus:ring-blue-600/20 focus:border-blue-600"
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-1"
                  tabIndex={-1}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>

              {/* Inline validation error */}
              {touched.confirmPassword && confirmPassword && !doPasswordsMatch && (
                <p className="mt-1 text-[11px] text-red-600">
                  Passwords do not match.
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
                    <span>Creating Account...</span>
                  </>
                ) : (
                  <span>Create Account</span>
                )}
              </button>
            </div>
          </form>

          {/* Links */}
          <div className="mt-6 pt-5 border-t border-slate-200 text-center space-y-2">
            <p className="text-xs text-slate-600">
              Already have an account?{" "}
              <Link
                to="/login"
                className="font-bold text-blue-700 hover:text-blue-900 transition"
              >
                Sign In
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
            <span>End-to-end encrypted • Supabase Auth</span>
          </div>
        </div>
      </div>
    </div>
  );
}
