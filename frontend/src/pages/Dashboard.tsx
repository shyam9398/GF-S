import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Plus,
  FileCheck2,
  Clock,
  AlertTriangle,
  FolderOpen,
  ArrowRight,
  RefreshCw,
  Search,
  ExternalLink,
  ShieldCheck,
} from "lucide-react";
import { api } from "../services/api";
import { useTranslation } from "../i18n/I18nContext";

interface AnalysisItem {
  id: string;
  product_name: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export default function Dashboard() {
  const { t } = useTranslation();
  const [analyses, setAnalyses] = useState<AnalysisItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalyses = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.get<AnalysisItem[]>("/analyses");
      setAnalyses(res.data || []);
    } catch (err: unknown) {
      console.error("Failed to fetch analyses:", err);
      setError("Unable to load analyses from backend. Ensure backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalyses();
  }, []);

  const totalCount = analyses.length;
  const completedCount = analyses.filter(
    (a) => a.status?.toUpperCase() === "COMPLETED"
  ).length;
  const inProgressCount = analyses.filter(
    (a) =>
      a.status?.toUpperCase() === "PROCESSING" ||
      a.status?.toUpperCase() === "CREATED"
  ).length;
  const verificationCount = analyses.filter(
    (a) => a.status?.toUpperCase() === "NEEDS_VERIFICATION"
  ).length;

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 p-8 text-white shadow-md">
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-blue-200 backdrop-blur-md mb-4 border border-white/10">
            <ShieldCheck size={14} className="text-blue-300" />
            <span>{t("dash.badge", "Procurement Intelligence")} • SIH 2026 PS 26108</span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-white">
            {t("dash.hero_title", "Find the standards your specification needs.")}
          </h1>
          <p className="mt-3 text-base text-blue-100/90 leading-relaxed">
            {t(
              "dash.hero_desc",
              "Analyze procurement specifications and identify applicable Indian Standards (BIS) with traceable evidence and Quality Control Orders (QCO)."
            )}
          </p>

          <div className="mt-6 flex flex-wrap gap-4 items-center">
            <Link
              to="/analysis/new"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-blue-900 shadow-sm transition hover:bg-blue-50 active:scale-98"
            >
              <Plus size={18} />
              {t("dash.btn_new", "+ Start New Analysis")}
            </Link>
            <a
              href="https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-xl bg-blue-700/60 border border-blue-400/30 px-4 py-3 text-sm font-medium text-white transition hover:bg-blue-700 active:scale-98"
            >
              <ExternalLink size={16} />
              <span>Know Your Standards (BIS Portal)</span>
            </a>
          </div>
        </div>

        {/* Decorative corner accent */}
        <div className="absolute right-0 bottom-0 translate-x-12 translate-y-12 w-64 h-64 rounded-full bg-blue-500/10 blur-2xl pointer-events-none" />
      </section>

      {/* Metric Cards */}
      <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">
              {t("dash.stat_total", "Total Analyses")}
            </span>
            <FolderOpen size={18} className="text-blue-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-slate-900">
            {loading ? "..." : totalCount}
          </div>
          <div className="mt-1 text-xs text-slate-500">Recorded specifications</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">
              {t("dash.stat_completed", "Completed")}
            </span>
            <FileCheck2 size={18} className="text-emerald-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-emerald-700">
            {loading ? "..." : completedCount}
          </div>
          <div className="mt-1 text-xs text-slate-500">With verified recommendations</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">
              {t("dash.stat_pending", "In Progress")}
            </span>
            <Clock size={18} className="text-amber-500" />
          </div>
          <div className="mt-3 text-3xl font-black text-amber-700">
            {loading ? "..." : inProgressCount}
          </div>
          <div className="mt-1 text-xs text-slate-500">Queued or running</div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-xs font-semibold uppercase tracking-wider">
              {t("dash.stat_needs_verification", "Needs Verification")}
            </span>
            <AlertTriangle size={18} className="text-purple-600" />
          </div>
          <div className="mt-3 text-3xl font-black text-purple-700">
            {loading ? "..." : verificationCount}
          </div>
          <div className="mt-1 text-xs text-slate-500">Standards requiring review</div>
        </div>
      </section>

      {/* Recent Analyses Table */}
      <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-2xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-base font-bold text-slate-900">
              {t("dash.recent_title", "Recent Procurement Analyses")}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live tracking of specifications processed by the AI recommendation pipeline
            </p>
          </div>
          <button
            onClick={fetchAnalyses}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 transition"
          >
            <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
            {error}
          </div>
        )}

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">
            <RefreshCw size={24} className="mx-auto mb-2 animate-spin text-blue-600" />
            {t("loading", "Loading analyses...")}
          </div>
        ) : analyses.length === 0 ? (
          <div className="py-12 text-center">
            <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-400 mb-3">
              <Search size={22} />
            </div>
            <p className="text-sm font-semibold text-slate-700">
              {t("dash.recent_empty", "No analyses run yet.")}
            </p>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Start your first analysis by clicking the button below or using the navigation.
            </p>
            <Link
              to="/analysis/new"
              className="mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 transition"
            >
              <Plus size={15} />
              {t("dash.btn_new", "+ Start New Analysis")}
            </Link>
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 uppercase tracking-wider font-semibold">
                  <th className="py-3 px-3">{t("dash.col_product", "Product / Item")}</th>
                  <th className="py-3 px-3">{t("dash.col_status", "Pipeline Status")}</th>
                  <th className="py-3 px-3">{t("dash.col_date", "Date Created")}</th>
                  <th className="py-3 px-3 text-right">{t("dash.col_actions", "Actions")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium">
                {analyses.slice(0, 10).map((item) => {
                  const status = (item.status || "CREATED").toUpperCase();
                  const isCompleted = status === "COMPLETED";

                  return (
                    <tr key={item.id} className="hover:bg-slate-50 transition">
                      <td className="py-3.5 px-3">
                        <div className="font-bold text-slate-900 text-sm">
                          {item.product_name}
                        </div>
                        <div className="text-slate-500 text-[11px] line-clamp-1 max-w-md mt-0.5">
                          {item.description}
                        </div>
                      </td>
                      <td className="py-3.5 px-3">
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-bold ${
                            isCompleted
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : status === "PROCESSING"
                              ? "bg-blue-50 text-blue-700 border border-blue-200 animate-pulse"
                              : status === "FAILED"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-slate-100 text-slate-700 border border-slate-200"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${
                              isCompleted
                                ? "bg-emerald-500"
                                : status === "PROCESSING"
                                ? "bg-blue-500"
                                : status === "FAILED"
                                ? "bg-rose-500"
                                : "bg-slate-400"
                            }`}
                          />
                          {status}
                        </span>
                      </td>
                      <td className="py-3.5 px-3 text-slate-500">
                        {item.created_at
                          ? new Date(item.created_at).toLocaleDateString(undefined, {
                              year: "numeric",
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })
                          : "—"}
                      </td>
                      <td className="py-3.5 px-3 text-right">
                        <Link
                          to={
                            isCompleted
                              ? `/analysis/${item.id}/results`
                              : `/analysis/${item.id}/progress`
                          }
                          className="inline-flex items-center gap-1 rounded-md bg-slate-100 hover:bg-blue-50 hover:text-blue-700 px-3 py-1.5 text-xs font-semibold text-slate-700 transition"
                        >
                          {isCompleted
                            ? t("dash.view_results", "View Results")
                            : "Track Pipeline"}
                          <ArrowRight size={13} />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}