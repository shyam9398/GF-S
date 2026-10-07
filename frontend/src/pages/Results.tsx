import { useEffect, useState, useMemo } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  FileCheck2,
  FileText,
  FlaskConical,
  GitBranch,
  Layers,
  Loader2,
  Printer,
  Scale,
  Search,
  ShieldAlert,
  ShieldCheck,
  TestTube2,
  TriangleAlert,
  XCircle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

import { API_BASE_URL } from "../services/api";
import { useTranslation } from "../i18n/I18nContext";

export interface VersionInfo {
  published_on?: string | null;
  valid_upto?: string | null;
  review_on?: string | null;
  reaffirmation_year?: string | number | null;
  revision_count?: string | number | null;
  amendment_count?: string | number | null;
  withdraw_status?: number | string | null;
  withdraw_on?: string | null;
  superseded_by?: string | null;
  amendments?: unknown[];
  status_note?: string;
}

export interface CertificationInfo {
  status?: "MANDATORY" | "VOLUNTARY" | "VERIFY" | "NOT_FOUND" | string;
  scheme?: string;
  qco_name?: string;
  ministry?: string;
  gazette_notification?: string;
  effective_date?: string;
  source_note?: string;
  notes?: string;
}

export interface StandardResult {
  standard_number: string | null;
  standard_name: string | null;
  title?: string | null;
  classification: string;
  human_classification?: string | null;
  recommendation_level?: string;
  applicability_signal?: number | null;
  applicability_score?: number | null;
  compatibility?: string | null;
  compat_reason?: string;
  rejection_reason?: string;
  semantic_similarity?: number | null;
  lexical_match?: number | null;
  verification_required?: boolean;
  standard_role?: string;
  role_description?: string;
  lifecycle_status?: string;
  certification?: CertificationInfo;
  why_recommended?: string[];
  reasons?: string[];
  evidence?: string[];
  source_url?: string | null;
  revision?: string | null;
  amendments?: unknown[];
  version_information?: VersionInfo;
  version_lifecycle?: VersionInfo;
  related_standards?: Array<{
    standard_number?: string | null;
    standard_name?: string | null;
    relationship_type?: string | null;
  }>;
  normative_references?: Array<{
    standard_number?: string | null;
    standard_name?: string | null;
    relationship_type?: string | null;
  }>;
}

export interface RelationshipVerification {
  primary_standard?: {
    standard_number?: string;
    title?: string;
    applicability_score?: number;
  };
  normative_references?: Array<{
    standard_number?: string;
    title?: string;
    relationship?: string;
    evidence?: string;
  }>;
  allied_standards?: Array<{
    standard_number?: string;
    title?: string;
    relationship?: string;
    evidence?: string;
  }>;
}

export interface ResultsData {
  success?: boolean;
  status?: string;
  analysis_id?: string;
  input_summary?: {
    product_name?: string;
    application?: string;
    key_specifications?: string[];
  };
  primary_applicable?: StandardResult[];
  normative_references?: StandardResult[];
  allied_standards?: StandardResult[];
  related_supporting?: StandardResult[];
  needs_verification?: StandardResult[];
  not_applicable?: StandardResult[];
  recommended_standards?: StandardResult[];
  relationship_verifications?: RelationshipVerification[];
  processing?: {
    total_ms?: number;
    bis_search_ms?: number;
    ranking_ms?: number;
  };
  errors?: Array<{ stage?: string; message?: string }>;
}

export default function Results() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();

  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<
    "primary" | "normative" | "allied" | "supporting" | "verify" | "not_applicable" | "all"
  >("primary");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  useEffect(() => {
    let cancelled = false;

    async function loadResults() {
      if (!id) {
        setError("Analysis ID is missing.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch complete results from /api/analyses/{id}/results
        const res = await fetch(`${API_BASE_URL}/analyses/${id}/results`);
        if (!res.ok) {
          // Fallback to /api/analyses/{id}/results/summary
          const resSummary = await fetch(`${API_BASE_URL}/analyses/${id}/results/summary`);
          if (!resSummary.ok) {
            throw new Error(`Failed to load results (Status ${res.status})`);
          }
          const summaryJson = await resSummary.json();
          if (!cancelled) {
            setData(summaryJson);
          }
          return;
        }

        const json = await res.json();
        if (!cancelled) {
          setData(json);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load analysis results. Please verify backend status."
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadResults();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const toggleExpand = (standardKey: string) => {
    setExpandedCards((prev) => ({
      ...prev,
      [standardKey]: !prev[standardKey],
    }));
  };

  // Grouped standards with fallback normalization
  const primaryStandards: StandardResult[] = useMemo(() => {
    return data?.primary_applicable || (data as any)?.PRIMARY_APPLICABLE || [];
  }, [data]);

  const normativeStandards: StandardResult[] = useMemo(() => {
    return data?.normative_references || (data as any)?.NORMATIVE_REFERENCES || [];
  }, [data]);

  const alliedStandards: StandardResult[] = useMemo(() => {
    return data?.allied_standards || (data as any)?.ALLIED_STANDARDS || [];
  }, [data]);

  const supportingStandards: StandardResult[] = useMemo(() => {
    return (
      data?.related_supporting ||
      (data as any)?.supporting_standards ||
      (data as any)?.RELATED_SUPPORTING ||
      []
    );
  }, [data]);

  const verifyStandards: StandardResult[] = useMemo(() => {
    return data?.needs_verification || (data as any)?.NEEDS_VERIFICATION || [];
  }, [data]);

  const notApplicableStandards: StandardResult[] = useMemo(() => {
    return data?.not_applicable || (data as any)?.NOT_APPLICABLE || [];
  }, [data]);

  // Combined for active tab
  const displayedStandards = useMemo(() => {
    let list: StandardResult[] = [];
    switch (activeTab) {
      case "primary":
        list = primaryStandards;
        break;
      case "normative":
        list = normativeStandards;
        break;
      case "allied":
        list = alliedStandards;
        break;
      case "supporting":
        list = supportingStandards;
        break;
      case "verify":
        list = verifyStandards;
        break;
      case "not_applicable":
        list = notApplicableStandards;
        break;
      case "all":
        list = [
          ...primaryStandards,
          ...normativeStandards,
          ...alliedStandards,
          ...supportingStandards,
          ...verifyStandards,
          ...notApplicableStandards,
        ];
        break;
    }

    if (!searchQuery.trim()) return list;

    const query = searchQuery.toLowerCase();
    return list.filter((s) => {
      const num = (s.standard_number || "").toLowerCase();
      const name = (s.standard_name || s.title || "").toLowerCase();
      const role = (s.role_description || s.standard_role || "").toLowerCase();
      return num.includes(query) || name.includes(query) || role.includes(query);
    });
  }, [
    activeTab,
    primaryStandards,
    normativeStandards,
    alliedStandards,
    supportingStandards,
    verifyStandards,
    notApplicableStandards,
    searchQuery,
  ]);

  if (loading) {
    return (
      <div className="flex min-h-[500px] flex-col items-center justify-center space-y-4">
        <Loader2 size={36} className="animate-spin text-blue-600" />
        <p className="text-sm font-semibold text-slate-700">
          {t("loading", "Loading analysis results & BIS evidence...")}
        </p>
        <p className="text-xs text-slate-400">Verifying QCO Gazettes, Amendments and Roles...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center">
        <AlertCircle size={32} className="mx-auto text-rose-600 mb-2" />
        <h2 className="text-base font-bold text-rose-900">Analysis Results Unavailable</h2>
        <p className="mt-1 text-sm text-rose-700 max-w-md mx-auto">
          {error || "Could not retrieve the analysis output from the server."}
        </p>
        <div className="mt-4 flex justify-center gap-3">
          <Link
            to="/history"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <ArrowLeft size={14} /> Back to History
          </Link>
          <button
            onClick={() => window.location.reload()}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700"
          >
            Retry Loading
          </button>
        </div>
      </div>
    );
  }

  const productName =
    data.input_summary?.product_name ||
    (data as any)?.procurement?.product_name ||
    "Procurement Item";

  return (
    <div className="space-y-6">
      {/* Top Header / Actions Bar */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Link
              to="/history"
              className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-800 transition"
            >
              <ArrowLeft size={14} />
              {t("res.back", "Back to History")}
            </Link>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-bold text-blue-700 uppercase tracking-wider">
              {data.status === "completed" ? "Verified Assessment" : "Analysis Record"}
            </span>
          </div>
          <h1 className="mt-1 text-2xl font-black text-slate-900 sm:text-3xl">
            {productName}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Analysis ID: <code className="font-mono text-slate-700">{id}</code> • Standard Role Gate & QCO Verification Active
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => window.print()}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 shadow-2xs hover:bg-slate-50 transition"
          >
            <Printer size={15} />
            Print / Save PDF
          </button>
          <a
            href="https://www.services.bis.gov.in"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white shadow-2xs hover:bg-blue-700 transition"
          >
            <ExternalLink size={14} />
            BIS Care Portal
          </a>
        </div>
      </div>

      {/* Compliance Overview Card */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-2xs">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-2.5">
            <div className="grid h-8 w-8 place-items-center rounded-lg bg-blue-100 text-blue-700">
              <Scale size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                {t("res.overview", "Compliance Overview & Standard Separation")}
              </h2>
              <p className="text-xs text-slate-500">
                Strict separation between primary product specifications, normative test methods, and non-applicable standards
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 font-semibold text-emerald-700 border border-emerald-200">
              <CheckCircle2 size={13} />
              Role Gate Active
            </span>
          </div>
        </div>

        {/* 6-Way Category Summary Counters */}
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
          <button
            onClick={() => setActiveTab("primary")}
            className={`rounded-xl border p-3 text-left transition ${
              activeTab === "primary"
                ? "border-emerald-500 bg-emerald-50/70 shadow-2xs"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
              {t("res.tab_primary", "Primary Applicable")}
            </div>
            <div className="mt-1 text-2xl font-black text-emerald-700">
              {primaryStandards.length}
            </div>
            <div className="mt-0.5 text-[10px] text-emerald-600">Product Specifications</div>
          </button>

          <button
            onClick={() => setActiveTab("normative")}
            className={`rounded-xl border p-3 text-left transition ${
              activeTab === "normative"
                ? "border-cyan-500 bg-cyan-50/70 shadow-2xs"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="text-[11px] font-bold text-cyan-800 uppercase tracking-wider">
              {t("res.tab_normative", "Normative")}
            </div>
            <div className="mt-1 text-2xl font-black text-cyan-700">
              {normativeStandards.length}
            </div>
            <div className="mt-0.5 text-[10px] text-cyan-600">Test & Material Refs</div>
          </button>

          <button
            onClick={() => setActiveTab("allied")}
            className={`rounded-xl border p-3 text-left transition ${
              activeTab === "allied"
                ? "border-purple-500 bg-purple-50/70 shadow-2xs"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="text-[11px] font-bold text-purple-800 uppercase tracking-wider">
              {t("res.tab_allied", "Allied")}
            </div>
            <div className="mt-1 text-2xl font-black text-purple-700">
              {alliedStandards.length}
            </div>
            <div className="mt-0.5 text-[10px] text-purple-600">Family & System</div>
          </button>

          <button
            onClick={() => setActiveTab("supporting")}
            className={`rounded-xl border p-3 text-left transition ${
              activeTab === "supporting"
                ? "border-indigo-500 bg-indigo-50/70 shadow-2xs"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="text-[11px] font-bold text-indigo-800 uppercase tracking-wider">
              {t("res.tab_supporting", "Supporting")}
            </div>
            <div className="mt-1 text-2xl font-black text-indigo-700">
              {supportingStandards.length}
            </div>
            <div className="mt-0.5 text-[10px] text-indigo-600">Codes & Practices</div>
          </button>

          <button
            onClick={() => setActiveTab("verify")}
            className={`rounded-xl border p-3 text-left transition ${
              activeTab === "verify"
                ? "border-amber-500 bg-amber-50/70 shadow-2xs"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">
              {t("res.tab_verify", "Needs Verification")}
            </div>
            <div className="mt-1 text-2xl font-black text-amber-700">
              {verifyStandards.length}
            </div>
            <div className="mt-0.5 text-[10px] text-amber-600">Review Required</div>
          </button>

          <button
            onClick={() => setActiveTab("not_applicable")}
            className={`rounded-xl border p-3 text-left transition ${
              activeTab === "not_applicable"
                ? "border-rose-500 bg-rose-50/70 shadow-2xs"
                : "border-slate-200 bg-white hover:bg-slate-50"
            }`}
          >
            <div className="text-[11px] font-bold text-rose-800 uppercase tracking-wider">
              {t("res.tab_not_applicable", "Not Applicable")}
            </div>
            <div className="mt-1 text-2xl font-black text-rose-700">
              {notApplicableStandards.length}
            </div>
            <div className="mt-0.5 text-[10px] text-rose-600">Subtype Mismatch</div>
          </button>
        </div>
      </div>

      {/* Tabs and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1.5 border-b border-slate-200 pb-2 sm:border-0 sm:pb-0">
          <TabButton
            active={activeTab === "primary"}
            onClick={() => setActiveTab("primary")}
            label={t("res.tab_primary", "Primary Applicable")}
            count={primaryStandards.length}
            variant="emerald"
          />
          <TabButton
            active={activeTab === "normative"}
            onClick={() => setActiveTab("normative")}
            label={t("res.tab_normative", "Normative References")}
            count={normativeStandards.length}
            variant="cyan"
          />
          <TabButton
            active={activeTab === "allied"}
            onClick={() => setActiveTab("allied")}
            label={t("res.tab_allied", "Allied Standards")}
            count={alliedStandards.length}
            variant="purple"
          />
          <TabButton
            active={activeTab === "supporting"}
            onClick={() => setActiveTab("supporting")}
            label={t("res.tab_supporting", "Related Supporting")}
            count={supportingStandards.length}
            variant="indigo"
          />
          <TabButton
            active={activeTab === "verify"}
            onClick={() => setActiveTab("verify")}
            label={t("res.tab_verify", "Needs Verification")}
            count={verifyStandards.length}
            variant="amber"
          />
          <TabButton
            active={activeTab === "not_applicable"}
            onClick={() => setActiveTab("not_applicable")}
            label={t("res.tab_not_applicable", "Not Applicable")}
            count={notApplicableStandards.length}
            variant="rose"
          />
          <TabButton
            active={activeTab === "all"}
            onClick={() => setActiveTab("all")}
            label="All Standards"
            count={
              primaryStandards.length +
              normativeStandards.length +
              alliedStandards.length +
              supportingStandards.length +
              verifyStandards.length +
              notApplicableStandards.length
            }
            variant="slate"
          />
        </div>

        {/* Search inside standards */}
        <div className="relative min-w-[220px]">
          <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter standards by number/title..."
            className="w-full rounded-lg border border-slate-200 bg-white pl-8 pr-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:border-blue-500 focus:outline-hidden"
          />
        </div>
      </div>

      {/* Tab Context Explanation Banner */}
      {activeTab === "primary" && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-3.5 text-xs text-emerald-900 flex items-start gap-2.5">
          <ShieldCheck size={18} className="text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Standard Role Gate Enforced: </span>
            {t(
              "res.primary_desc",
              "These product specification standards directly govern the procurement item. Test methods, sampling, and headforms are categorized separately."
            )}
          </div>
        </div>
      )}

      {activeTab === "normative" && (
        <div className="rounded-xl border border-cyan-200 bg-cyan-50/50 p-3.5 text-xs text-cyan-900 flex items-start gap-2.5">
          <FileCheck2 size={18} className="text-cyan-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Normative Hierarchy: </span>
            {t(
              "res.normative_desc",
              "Standards explicitly cited within the primary specification for test procedures, raw material verification, or sampling."
            )}
          </div>
        </div>
      )}

      {activeTab === "not_applicable" && (
        <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-3.5 text-xs text-rose-900 flex items-start gap-2.5">
          <XCircle size={18} className="text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Eliminated by Product Subtype Filter: </span>
            {t(
              "res.not_applicable_desc",
              "Standards retrieved during lexical or broad search, but ruled out due to incompatible product subtype or domain mismatch."
            )}
          </div>
        </div>
      )}

      {/* Standards List */}
      {displayedStandards.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-12 text-center shadow-2xs">
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-slate-100 text-slate-400 mb-3">
            <FileText size={22} />
          </div>
          <h3 className="text-sm font-bold text-slate-700">
            {t("res.empty_category", "No standards found in this category.")}
          </h3>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Try switching tabs or clearing your filter query.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {displayedStandards.map((std, idx) => {
            const cardKey = `${std.standard_number || "std"}-${idx}`;
            const isExpanded = !!expandedCards[cardKey];
            const isPrimary = std.classification === "PRIMARY_APPLICABLE" || activeTab === "primary";

            return (
              <StandardCard
                key={cardKey}
                standard={std}
                isPrimary={isPrimary}
                isExpanded={isExpanded}
                onToggleExpand={() => toggleExpand(cardKey)}
              />
            );
          })}
        </div>
      )}

      {/* Relationship Verification Cross-Reference Section */}
      {data.relationship_verifications && data.relationship_verifications.length > 0 && (
        <div className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-2xs">
          <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
            <GitBranch size={18} className="text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Hierarchical Relationship Graph & Normative Verification
            </h3>
          </div>

          <div className="mt-4 space-y-4">
            {data.relationship_verifications.map((rel, rIdx) => (
              <div
                key={rIdx}
                className="rounded-xl border border-slate-200 bg-slate-50/50 p-4"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-900">
                    Primary: {rel.primary_standard?.standard_number || "Standard"}
                  </span>
                  <span className="text-xs text-slate-500">
                    {rel.primary_standard?.title}
                  </span>
                </div>

                {rel.normative_references && rel.normative_references.length > 0 && (
                  <div className="mt-3">
                    <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                      Verified Normative References:
                    </p>
                    <div className="mt-1.5 flex flex-wrap gap-2">
                      {rel.normative_references.map((norm, nIdx) => (
                        <div
                          key={nIdx}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-200 bg-cyan-50 px-2.5 py-1 text-xs text-cyan-800"
                        >
                          <FileCheck2 size={12} className="text-cyan-600" />
                          <span className="font-mono font-bold">{norm.standard_number}</span>
                          <span className="text-slate-500 text-[11px]">({norm.relationship || "Normative"})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------------------
// Subcomponents
// ----------------------------------------------------------------------------

function TabButton({
  active,
  onClick,
  label,
  count,
  variant,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  count: number;
  variant: "emerald" | "cyan" | "purple" | "indigo" | "amber" | "rose" | "slate";
}) {
  const getBadgeClass = () => {
    switch (variant) {
      case "emerald":
        return active ? "bg-emerald-600 text-white" : "bg-emerald-100 text-emerald-800";
      case "cyan":
        return active ? "bg-cyan-600 text-white" : "bg-cyan-100 text-cyan-800";
      case "purple":
        return active ? "bg-purple-600 text-white" : "bg-purple-100 text-purple-800";
      case "indigo":
        return active ? "bg-indigo-600 text-white" : "bg-indigo-100 text-indigo-800";
      case "amber":
        return active ? "bg-amber-600 text-white" : "bg-amber-100 text-amber-800";
      case "rose":
        return active ? "bg-rose-600 text-white" : "bg-rose-100 text-rose-800";
      default:
        return active ? "bg-slate-700 text-white" : "bg-slate-200 text-slate-800";
    }
  };

  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
        active
          ? "bg-slate-900 text-white shadow-xs"
          : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`}
    >
      <span>{label}</span>
      <span
        className={`rounded-full px-1.5 py-0.2 text-[10px] font-bold ${getBadgeClass()}`}
      >
        {count}
      </span>
    </button>
  );
}

function StandardCard({
  standard,
  isPrimary,
  isExpanded,
  onToggleExpand,
}: {
  standard: StandardResult;
  isPrimary: boolean;
  isExpanded: boolean;
  onToggleExpand: () => void;
}) {
  const { t } = useTranslation();
  const cert = standard.certification;
  const isMandatoryQCO = cert?.status === "MANDATORY";
  const isVoluntary = cert?.status === "VOLUNTARY";
  const isVerifyQCO = cert?.status === "VERIFY";

  const score = standard.applicability_score ?? standard.applicability_signal ?? null;
  const roleName = standard.role_description || standard.standard_role || "Product Specification";
  const lifecycle = standard.lifecycle_status || "Active";
  const reaffirmYear =
    standard.version_information?.reaffirmation_year ||
    standard.version_lifecycle?.reaffirmation_year;
  const amendments =
    standard.version_information?.amendments ||
    standard.version_lifecycle?.amendments ||
    standard.amendments ||
    [];

  const whyList = standard.why_recommended || standard.reasons || [];

  const bisPortalUrl =
    standard.source_url ||
    `https://www.services.bis.gov.in/php/BIS_2.0/bisconnect/knowyourstandards/indian_standards/isdetails?is_number=${encodeURIComponent(
      standard.standard_number || ""
    )}`;

  return (
    <div
      className={`rounded-xl border transition-all ${
        isPrimary
          ? "border-emerald-300 bg-white shadow-sm ring-1 ring-emerald-200"
          : "border-slate-200 bg-white shadow-2xs hover:border-slate-300"
      }`}
    >
      {/* Top Banner for Primary */}
      {isPrimary && (
        <div className="flex items-center justify-between bg-emerald-50 px-5 py-2 border-b border-emerald-100 rounded-t-xl text-xs font-bold text-emerald-800">
          <span className="flex items-center gap-1.5">
            <CheckCircle2 size={14} className="text-emerald-600" />
            PRIMARY APPLICABLE STANDARD • PRODUCT SPECIFICATION
          </span>
          {score !== null && (
            <span className="rounded-full bg-emerald-600 px-2 py-0.5 text-[11px] text-white">
              {score}% Match
            </span>
          )}
        </div>
      )}

      <div className="p-5">
        {/* Main Info Row */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-base font-extrabold text-slate-900 tracking-tight">
                {standard.standard_number || "IS Standard"}
              </span>

              {/* Standard Role Tag */}
              <span
                className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-semibold border ${
                  standard.standard_role === "PRODUCT_SPECIFICATION"
                    ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                    : standard.standard_role === "TEST_METHOD"
                    ? "bg-cyan-50 text-cyan-800 border-cyan-200"
                    : standard.standard_role === "SAMPLING_METHOD"
                    ? "bg-purple-50 text-purple-800 border-purple-200"
                    : standard.standard_role === "HEADFORM"
                    ? "bg-amber-50 text-amber-800 border-amber-200"
                    : standard.standard_role === "MATERIAL_SPECIFICATION"
                    ? "bg-indigo-50 text-indigo-800 border-indigo-200"
                    : "bg-slate-100 text-slate-700 border-slate-200"
                }`}
              >
                {roleName}
              </span>

              {/* Quality Control Order (QCO) Badge */}
              {isMandatoryQCO ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-2.5 py-0.5 text-[11px] font-bold text-white shadow-2xs">
                  <ShieldCheck size={12} />
                  {t("res.qco_badge_mandatory", "MANDATORY QCO")}
                </span>
              ) : isVoluntary ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-slate-100 border border-slate-200 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                  {t("res.qco_badge_voluntary", "VOLUNTARY")}
                </span>
              ) : isVerifyQCO ? (
                <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 border border-amber-200 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
                  <TriangleAlert size={12} />
                  {t("res.qco_badge_verify", "VERIFY QCO")}
                </span>
              ) : null}

              {/* Lifecycle Badge */}
              <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600">
                {lifecycle}
                {reaffirmYear ? ` (${reaffirmYear})` : ""}
              </span>
            </div>

            <h3 className="mt-2 text-sm font-bold text-slate-800 leading-snug">
              {standard.standard_name || standard.title || "Untitled Standard"}
            </h3>
          </div>

          {/* Right Action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            <a
              href={bisPortalUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-50 transition"
            >
              <span>{t("res.view_bis", "View in BIS Portal")}</span>
              <ExternalLink size={13} />
            </a>

            <button
              onClick={onToggleExpand}
              className="p-1.5 rounded-lg border border-slate-200 text-slate-500 hover:bg-slate-50 transition"
              aria-label="Expand details"
            >
              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>
        </div>

        {/* Rejection / Mismatch Banner if Not Applicable */}
        {(standard.rejection_reason || standard.compat_reason) && (
          <div className="mt-3 rounded-lg border border-rose-200 bg-rose-50/70 p-2.5 text-xs text-rose-800">
            <span className="font-bold">Subtype Verification: </span>
            {standard.rejection_reason || standard.compat_reason}
          </div>
        )}

        {/* Why Recommended Section */}
        {whyList.length > 0 && (
          <div className="mt-3">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              {t("res.why", "Why Recommended:")}
            </p>
            <ul className="mt-1 space-y-1 text-xs text-slate-600">
              {whyList.slice(0, isExpanded ? 10 : 2).map((reason, rIdx) => (
                <li key={rIdx} className="flex items-start gap-1.5">
                  <span className="text-emerald-500 font-bold">•</span>
                  <span>{reason}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Detailed Expanded Drawer */}
        {isExpanded && (
          <div className="mt-4 pt-4 border-t border-slate-100 space-y-4 text-xs">
            {/* QCO Gazette Details */}
            {cert && (cert.qco_name || cert.gazette_notification) && (
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/40 p-3">
                <p className="font-bold text-emerald-900">
                  Quality Control Order (Gazette Notification)
                </p>
                <div className="mt-1.5 grid grid-cols-1 sm:grid-cols-2 gap-2 text-slate-700">
                  {cert.qco_name && (
                    <div>
                      <span className="text-slate-400">Order: </span>
                      <span className="font-semibold">{cert.qco_name}</span>
                    </div>
                  )}
                  {cert.ministry && (
                    <div>
                      <span className="text-slate-400">Ministry: </span>
                      <span className="font-semibold">{cert.ministry}</span>
                    </div>
                  )}
                  {cert.gazette_notification && (
                    <div>
                      <span className="text-slate-400">Gazette S.O.: </span>
                      <span className="font-mono">{cert.gazette_notification}</span>
                    </div>
                  )}
                  {cert.effective_date && (
                    <div>
                      <span className="text-slate-400">Effective Date: </span>
                      <span>{cert.effective_date}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Version & Amendments */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-100">
              <div>
                <span className="text-slate-400 text-[11px]">Reaffirmation:</span>
                <p className="font-semibold text-slate-800">{reaffirmYear || "Active"}</p>
              </div>
              <div>
                <span className="text-slate-400 text-[11px]">Amendments:</span>
                <p className="font-semibold text-slate-800">
                  {amendments.length > 0 ? `${amendments.length} Issued` : "None"}
                </p>
              </div>
              <div>
                <span className="text-slate-400 text-[11px]">Semantic Match:</span>
                <p className="font-semibold text-slate-800">
                  {standard.semantic_similarity !== undefined
                    ? `${Math.round((standard.semantic_similarity || 0) * 100)}%`
                    : "—"}
                </p>
              </div>
              <div>
                <span className="text-slate-400 text-[11px]">Subtype Status:</span>
                <p className="font-semibold text-slate-800">
                  {standard.compatibility || "Direct Match"}
                </p>
              </div>
            </div>

            {/* Normative References Embedded */}
            {standard.normative_references && standard.normative_references.length > 0 && (
              <div>
                <p className="font-bold text-slate-800 mb-1">
                  Normative References Cited:
                </p>
                <div className="flex flex-wrap gap-2">
                  {standard.normative_references.map((norm, nIdx) => (
                    <span
                      key={nIdx}
                      className="rounded-md border border-slate-200 bg-white px-2 py-1 font-mono text-[11px] text-slate-700"
                    >
                      {norm.standard_number || norm.standard_name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}