import { useEffect, useState } from "react";
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
  Loader2,
  Scale,
  ShieldCheck,
  TestTube2,
  TriangleAlert,
} from "lucide-react";

type StandardResult = {
  standard_number: string | null;
  standard_name: string | null;
  title?: string | null;
  classification: string;
  human_classification?: string | null;
  recommendation_level: string;
  applicability_signal: number | null;
  applicability_score?: number | null;
  lexical_match: number | null;
  verification_required: boolean;
  why_recommended?: string[];
  evidence?: string[];
  source_url?: string | null;
  reasons: string[];
  revision?: string | null;
  amendments?: unknown[];
  version_information: {
    published_on?: string | null;
    valid_upto?: string | null;
    review_on?: string | null;
    reaffirmation_year?: string | null;
    revision_count?: string | number | null;
    amendment_count?: string | number | null;
    withdraw_status?: number | string | null;
    withdraw_on?: string | null;
    superseded_by?: string | null;
    amendments?: unknown[];
  };
  related_standards: Array<{
    standard_number?: string | null;
    standard_name?: string | null;
    relationship_type?: string | null;
    source_type?: string | null;
  }>;
  normative_references?: Array<{
    standard_number?: string | null;
    standard_name?: string | null;
    relationship_type?: string | null;
  }>;
  conformity: {
    license_records?: number;
    crs_records?: number;
    mcs_records?: number;
    laboratory_records?: number;
    license_evidence_available?: boolean;
    crs_evidence_available?: boolean;
    mcs_evidence_available?: boolean;
    laboratory_evidence_available?: boolean;
    note?: string;
  };
  evidence_summary: {
    available?: string[];
    unavailable?: string[];
    error_count?: number;
  };
};

type ResultsResponse = {
  success?: boolean;
  status?: string;
  standards?: StandardResult[];
  recommended_standards?: StandardResult[];
  summary?: Record<string, number>;
  evidence_graph?: {
    nodes?: unknown[];
    edges?: unknown[];
  };
  coverage?: {
    candidate_count?: number;
    classification_counts?: Record<string, number>;
  };
  disclaimer?: string;
  errors?: Array<{
    stage?: string;
    message?: string;
  }>;
};

import { API_BASE_URL } from "../services/api";

const API_URL = API_BASE_URL;

function formatClassification(value: string) {
  return value
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatDate(value?: string | null) {
  if (!value) return "Not available";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function classificationStyle(classification: string, humanClass?: string | null) {
  if (humanClass === "Highly Applicable" || classification === "DIRECTLY_APPLICABLE") {
    return {
      container: "border-emerald-200 bg-emerald-50 text-emerald-700",
      icon: CheckCircle2,
    };
  }
  if (humanClass === "Applicable") {
    return {
      container: "border-blue-200 bg-blue-50 text-blue-700",
      icon: CheckCircle2,
    };
  }
  if (humanClass === "Related" || classification === "RELATED_SUPPORTING") {
    return {
      container: "border-indigo-200 bg-indigo-50 text-indigo-700",
      icon: GitBranch,
    };
  }

  switch (classification) {
    case "TEST_METHOD":
      return {
        container: "border-violet-200 bg-violet-50 text-violet-700",
        icon: TestTube2,
      };

    case "SAMPLING_METHOD":
      return {
        container: "border-indigo-200 bg-indigo-50 text-indigo-700",
        icon: FlaskConical,
      };

    case "SAFETY_RELATED":
      return {
        container: "border-orange-200 bg-orange-50 text-orange-700",
        icon: ShieldCheck,
      };

    case "NORMATIVE_REFERENCE":
      return {
        container: "border-cyan-200 bg-cyan-50 text-cyan-700",
        icon: FileCheck2,
      };

    case "NEEDS_VERIFICATION":
      return {
        container: "border-amber-200 bg-amber-50 text-amber-700",
        icon: TriangleAlert,
      };

    default:
      return {
        container: "border-slate-200 bg-slate-50 text-slate-700",
        icon: FileText,
      };
  }
}

function EvidenceBadge({
  label,
  available,
}: {
  label: string;
  available: boolean;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium ${
        available
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-slate-200 bg-slate-50 text-slate-500"
      }`}
    >
      {available ? (
        <CheckCircle2 className="h-3.5 w-3.5" />
      ) : (
        <AlertCircle className="h-3.5 w-3.5" />
      )}

      {label}
    </span>
  );
}

function SummaryCard({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-xl border border-line bg-white p-5 shadow-soft">
      <p className="text-xs font-medium uppercase tracking-wide text-muted">
        {label}
      </p>

      <p className="mt-2 text-2xl font-semibold text-ink">
        {value}
      </p>
    </div>
  );
}

export default function Results() {
  const { id } = useParams<{ id: string }>();

  const [data, setData] = useState<ResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

        const response = await fetch(
          `${API_URL}/analyses/${id}/results/summary`,
        );

        if (!response.ok) {
          let message = "Unable to load analysis results.";

          try {
            const body = await response.json();

            if (typeof body?.detail === "string") {
              message = body.detail;
            } else if (body?.detail?.message) {
              message = body.detail.message;
            }
          } catch {
            // Keep default error message.
          }

          throw new Error(message);
        }

        const result = (await response.json()) as ResultsResponse;

        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load analysis results.",
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

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>

        <div className="rounded-xl border border-line bg-white p-10 text-center shadow-soft">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-brand" />

          <h2 className="mt-4 text-lg font-semibold text-ink">
            Loading analysis results
          </h2>

          <p className="mt-2 text-sm text-muted">
            Retrieving official BIS evidence and recommendations.
          </p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-6">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>

        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 text-red-600" />
            <div>
              <h2 className="font-semibold text-red-800">
                Failed to load results
              </h2>
              <p className="mt-1 text-sm text-red-700">
                {error || "An unexpected error occurred."}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const standards = data.standards || data.recommended_standards || [];

  const directCount =
    standards.filter(
      (s) =>
        s.classification === "DIRECTLY_APPLICABLE" ||
        s.human_classification === "Highly Applicable",
    ).length;

  const supportingCount =
    standards.filter(
      (s) =>
        s.classification === "RELATED_SUPPORTING" ||
        s.human_classification === "Applicable",
    ).length;

  const verificationCount =
    standards.filter(
      (s) =>
        s.verification_required ||
        s.classification === "NEEDS_VERIFICATION",
    ).length;

  const testMethodCount =
    standards.filter((s) => s.classification === "TEST_METHOD").length;

  return (
    <div className="space-y-8">
      {/* Back & Header */}
      <div>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">
            Applicable Indian Standards
          </p>

          <h1 className="mt-2 text-3xl font-semibold text-ink">
            BIS Recommendations & Evidence
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            Identified directly from the authoritative Bureau of Indian Standards (BIS) database.
          </p>

          <p className="mt-1 text-xs text-muted">Analysis ID: {id}</p>
        </div>

        <Link
          to="/analysis/new"
          className="inline-flex w-fit rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          New Analysis
        </Link>
      </div>

      {/* Summary Metrics */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard label="Recommended Standards" value={standards.length} />
        <SummaryCard label="Highly Applicable" value={directCount} />
        <SummaryCard label="Applicable / Supporting" value={supportingCount} />
        <SummaryCard label="Needs Verification" value={verificationCount} />
      </div>

      {/* Standards List */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-ink">Recommended Standards</h2>
          <p className="mt-1 text-sm text-muted">
            Ranked deterministically by product match, application scope, technical requirements, materials, and safety parameters.
          </p>
        </div>

        {standards.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-soft">
            <FileText className="mx-auto h-10 w-10 text-slate-400" />
            <h3 className="mt-4 text-base font-semibold text-slate-800">
              No matching Indian Standards were retrieved
            </h3>
            <p className="mt-2 max-w-md mx-auto text-sm text-muted">
              The BIS repository search returned 0 candidates matching the generated procurement queries.
              Try adjusting the product name, keywords, or specifications in a new analysis.
            </p>
            <div className="mt-6">
              <Link
                to="/analysis/new"
                className="inline-flex rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Refine Procurement Specification
              </Link>
            </div>
          </div>
        ) : (
          standards.map((standard, index) => {
            const humanClass =
              standard.human_classification ||
              formatClassification(standard.classification);

            const style = classificationStyle(
              standard.classification,
              standard.human_classification,
            );

            const StatusIcon = style.icon;
            const version = standard.version_information || {};
            const conformity = standard.conformity || {};
            const scorePct =
              standard.applicability_score ??
              (standard.applicability_signal != null
                ? Math.round(standard.applicability_signal * 100)
                : 75);

            const whyList =
              standard.why_recommended && standard.why_recommended.length > 0
                ? standard.why_recommended
                : standard.reasons;

            const evidenceList = standard.evidence || [];

            return (
              <article
                key={`${standard.standard_number}-${index}`}
                className="rounded-xl border border-line bg-white p-6 shadow-soft transition-shadow hover:shadow-md"
              >
                {/* Header */}
                <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="rounded-md bg-blue-50 px-3 py-1 font-mono text-sm font-bold text-blue-900 border border-blue-200">
                        {standard.standard_number || "Standard Number Unavailable"}
                      </span>

                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold ${style.container}`}
                      >
                        <StatusIcon className="h-3.5 w-3.5" />
                        {humanClass}
                      </span>

                      {/* Applicability Score Pill */}
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 border border-slate-200">
                        <Scale className="h-3 w-3 text-brand" />
                        Applicability Score: {scorePct}%
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-ink leading-snug">
                      {standard.title || standard.standard_name || "Standard Title Unavailable"}
                    </h3>

                    {standard.recommendation_level && (
                      <p className="text-xs text-muted">
                        Recommendation Tier: {standard.recommendation_level}
                      </p>
                    )}
                  </div>

                  {/* Actions / BIS Portal Link */}
                  <div className="flex flex-col sm:flex-row gap-2 shrink-0">
                    {standard.source_url && (
                      <a
                        href={standard.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-line bg-slate-50 px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                      >
                        <ExternalLink className="h-3.5 w-3.5 text-brand" />
                        BIS Portal Reference
                      </a>
                    )}

                    {standard.verification_required && (
                      <div className="inline-flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800">
                        <TriangleAlert className="h-3.5 w-3.5" />
                        Verification Required
                      </div>
                    )}
                  </div>
                </div>

                {/* Why Recommended Section (Section 17) */}
                {whyList && whyList.length > 0 && (
                  <div className="mt-6 rounded-lg bg-blue-50/50 border border-blue-100 p-4">
                    <h4 className="text-sm font-semibold text-blue-950 flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-brand" />
                      Why This Standard Is Recommended
                    </h4>

                    <div className="mt-2.5 space-y-1.5">
                      {whyList.map((reason, rIdx) => (
                        <div key={rIdx} className="flex items-start gap-2 text-sm text-slate-700">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />
                          <span>{reason}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Evidence Supporting Recommendation (Section 17) */}
                {evidenceList && evidenceList.length > 0 && (
                  <div className="mt-4 rounded-lg bg-emerald-50/40 border border-emerald-100 p-4">
                    <h4 className="text-sm font-semibold text-emerald-950 flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-emerald-600" />
                      Evidence & BIS Traceability
                    </h4>

                    <div className="mt-2.5 space-y-1.5">
                      {evidenceList.map((ev, evIdx) => (
                        <div key={evIdx} className="flex items-start gap-2 text-sm text-emerald-900">
                          <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-600" />
                          <span>{ev}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Version and Status Evidence */}
                <div className="mt-6 border-t border-line pt-6">
                  <h4 className="text-sm font-semibold text-ink">
                    Version, Amendments & Status
                  </h4>

                  <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                      <p className="text-xs text-muted">Publication Date</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {formatDate(version.published_on)}
                      </p>
                    </div>

                    <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                      <p className="text-xs text-muted">Revision Level</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {version.revision_count || standard.revision || "Original"}
                      </p>
                    </div>

                    <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                      <p className="text-xs text-muted">Amendments / Corrigenda</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {version.amendment_count ??
                          (standard.amendments ? standard.amendments.length : "None recorded")}
                      </p>
                    </div>

                    <div className="rounded-lg bg-slate-50 p-3 border border-slate-100">
                      <p className="text-xs text-muted">Reaffirmation</p>
                      <p className="mt-1 text-sm font-semibold text-slate-800">
                        {version.reaffirmation_year || "Current"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Related Standards & Normative References */}
                {standard.related_standards && standard.related_standards.length > 0 && (
                  <div className="mt-6 border-t border-line pt-6">
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-brand" />
                      <h4 className="text-sm font-semibold text-ink">
                        Allied & Related Standards ({standard.related_standards.length})
                      </h4>
                    </div>

                    <div className="mt-3 grid gap-2.5 sm:grid-cols-2">
                      {standard.related_standards.slice(0, 6).map((related, relatedIndex) => (
                        <div
                          key={relatedIndex}
                          className="rounded-lg border border-line bg-slate-50 p-3"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="font-mono text-xs font-bold text-slate-800">
                              {related.standard_number || "Reference"}
                            </span>
                            {related.relationship_type && (
                              <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                                {formatClassification(related.relationship_type)}
                              </span>
                            )}
                          </div>
                          {related.standard_name && (
                            <p className="mt-1 text-xs text-muted line-clamp-2">
                              {related.standard_name}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Conformity Evidence */}
                <div className="mt-6 border-t border-line pt-6">
                  <h4 className="text-sm font-semibold text-ink">
                    BIS Certification & Conformity
                  </h4>

                  <div className="mt-3 flex flex-wrap gap-2">
                    <EvidenceBadge
                      label={`Active Licences: ${conformity.license_records ?? 0}`}
                      available={conformity.license_evidence_available ?? false}
                    />
                    <EvidenceBadge
                      label={`CRS Records: ${conformity.crs_records ?? 0}`}
                      available={conformity.crs_evidence_available ?? false}
                    />
                    <EvidenceBadge
                      label={`MCS Schemes: ${conformity.mcs_records ?? 0}`}
                      available={conformity.mcs_evidence_available ?? false}
                    />
                    <EvidenceBadge
                      label={`Recognized Labs: ${conformity.laboratory_records ?? 0}`}
                      available={conformity.laboratory_evidence_available ?? false}
                    />
                  </div>

                  {conformity.note && (
                    <p className="mt-2 text-xs text-muted">{conformity.note}</p>
                  )}
                </div>
              </article>
            );
          })
        )}
      </div>

      {/* Disclaimer */}
      {data.disclaimer && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
          <div className="flex items-start gap-3">
            <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-700" />
            <div>
              <h3 className="text-sm font-semibold text-amber-900">
                Official Disclaimer
              </h3>
              <p className="mt-1 text-sm leading-6 text-amber-800">
                {data.disclaimer}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}