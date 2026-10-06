import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  RefreshCw,
} from "lucide-react";

import { API_BASE_URL } from "../services/api";

const API_URL = API_BASE_URL;

type Analysis = {
  id: string;
  product_name: string;
  description: string;
  quantity?: number | null;
  status: string;
  created_at?: string;
  updated_at?: string;
};

type ReportSummary = {
  analysis_id?: string;
  product_name?: string;

  total_candidates?: number;
  direct_count?: number;
  supporting_count?: number;
  needs_verification_count?: number;

  coverage?: {
    discovered_queries?: number;
    unique_candidates?: number;
    enriched_candidates?: number;
    evaluated_candidates?: number;
    coverage_score?: number;
  };

  frontend?: {
    total_candidates?: number;
    direct_count?: number;
    supporting_count?: number;
    needs_verification_count?: number;
    coverage?: unknown;
    standards?: unknown[];
  };

  standards?: unknown[];
};

type ReportItem = {
  analysis: Analysis;
  summary: ReportSummary | null;
};

export default function Reports() {
  const [reports, setReports] =
    useState<ReportItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  async function loadReports() {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_URL}/analyses`,
      );

      if (!response.ok) {
        throw new Error(
          "Unable to load analyses.",
        );
      }

      const data = await response.json();

      const analyses: Analysis[] =
        Array.isArray(data)
          ? data
          : Array.isArray(data?.items)
            ? data.items
            : Array.isArray(data?.analyses)
              ? data.analyses
              : [];

      const completed =
        analyses.filter(
          (analysis) =>
            analysis.status?.toUpperCase() ===
            "COMPLETED",
        );

      const reportResults =
        await Promise.all(
          completed.map(
            async (analysis) => {
              try {
                const result =
                  await fetch(
                    `${API_URL}/analyses/${analysis.id}/results/summary`,
                  );

                if (!result.ok) {
                  return {
                    analysis,
                    summary: null,
                  };
                }

                const summary =
                  await result.json();

                return {
                  analysis,
                  summary,
                };
              } catch {
                return {
                  analysis,
                  summary: null,
                };
              }
            },
          ),
        );

      setReports(reportResults);
    } catch (error) {
      console.error(
        "Failed to load reports:",
        error,
      );

      setError(
        "Unable to load reports. Make sure the FastAPI backend is running on port 8000.",
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReports();
  }, []);

  return (
    <div className="space-y-6">
      {/* ----------------------------------------------------------
          Header
      ---------------------------------------------------------- */}

      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-700">
            Documentation
          </p>

          <h1 className="mt-2 text-3xl font-semibold text-ink">
            Reports
          </h1>

          <p className="mt-2 text-sm text-muted">
            Access generated procurement recommendation
            reports from completed analyses.
          </p>
        </div>

        <button
          type="button"
          onClick={loadReports}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <RefreshCw
            className={`h-4 w-4 ${
              loading
                ? "animate-spin"
                : ""
            }`}
          />

          Refresh
        </button>
      </div>

      {/* ----------------------------------------------------------
          Error
      ---------------------------------------------------------- */}

      {error && (
        <div className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />

          <div>
            <p className="text-sm font-medium text-red-800">
              Unable to load reports
            </p>

            <p className="mt-1 text-sm text-red-700">
              {error}
            </p>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------
          Loading
      ---------------------------------------------------------- */}

      {loading && (
        <div className="rounded-xl border border-line bg-white p-10 text-center shadow-soft">
          <Loader2 className="mx-auto h-7 w-7 animate-spin text-brand" />

          <p className="mt-3 text-sm font-medium text-slate-900">
            Loading reports...
          </p>

          <p className="mt-1 text-sm text-muted">
            Retrieving completed procurement analyses.
          </p>
        </div>
      )}

      {/* ----------------------------------------------------------
          Empty
      ---------------------------------------------------------- */}

      {!loading &&
        !error &&
        reports.length === 0 && (
          <div className="rounded-xl border border-line bg-white p-10 text-center shadow-soft">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
              <FileText className="h-6 w-6 text-slate-500" />
            </div>

            <p className="mt-4 text-sm font-semibold text-slate-900">
              No reports generated
            </p>

            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
              Reports will become available after a
              procurement analysis has completed successfully.
            </p>

            <Link
              to="/analysis/new"
              className="mt-5 inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
            >
              Create Analysis
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        )}

      {/* ----------------------------------------------------------
          Report Cards
      ---------------------------------------------------------- */}

      {!loading &&
        reports.length > 0 && (
          <div className="space-y-4">
            {reports.map(
              ({
                analysis,
                summary,
              }) => (
                <ReportCard
                  key={analysis.id}
                  analysis={analysis}
                  summary={summary}
                />
              ),
            )}
          </div>
        )}
    </div>
  );
}

/* ================================================================
   Report Card
================================================================ */

function ReportCard({
  analysis,
  summary,
}: {
  analysis: Analysis;
  summary: ReportSummary | null;
}) {
  const totalCandidates =
    getNumber(
      summary,
      "total_candidates",
    );

  const directCount =
    getNumber(
      summary,
      "direct_count",
    );

  const supportingCount =
    getNumber(
      summary,
      "supporting_count",
    );

  const needsVerification =
    getNumber(
      summary,
      "needs_verification_count",
    );

  const coverage =
    getCoverage(summary);

  return (
    <article className="rounded-xl border border-line bg-white p-6 shadow-soft">
      {/* Header */}

      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-blue-50">
            <FileText className="h-5 w-5 text-brand" />
          </div>

          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold text-slate-900">
              {analysis.product_name}
            </h2>

            <p className="mt-1 text-sm text-muted">
              {formatDate(
                analysis.created_at,
              )}
              {analysis.quantity
                ? ` • Quantity: ${analysis.quantity}`
                : ""}
            </p>

            <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">
              {analysis.description}
            </p>
          </div>
        </div>

        <div className="inline-flex shrink-0 items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-700">
          <CheckCircle2 className="h-3.5 w-3.5" />
          Completed
        </div>
      </div>

      {/* Metrics */}

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric
          label="Standards Evaluated"
          value={totalCandidates}
        />

        <Metric
          label="Directly Applicable"
          value={directCount}
        />

        <Metric
          label="Supporting"
          value={supportingCount}
        />

        <Metric
          label="Needs Verification"
          value={needsVerification}
        />
      </div>

      {/* Coverage */}

      {coverage !== null && (
        <div className="mt-5 rounded-lg bg-slate-50 p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-slate-800">
                Evidence Coverage
              </p>

              <p className="mt-1 text-xs text-muted">
                Coverage reported by the analysis pipeline.
              </p>
            </div>

            <p className="text-sm font-semibold text-slate-900">
              {formatCoverage(
                coverage,
              )}
            </p>
          </div>

          <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-brand transition-all"
              style={{
                width: `${Math.min(
                  Math.max(
                    coverage,
                    0,
                  ),
                  100,
                )}%`,
              }}
            />
          </div>
        </div>
      )}

      {/* Actions */}

      <div className="mt-6 flex justify-end">
        <Link
          to={`/analysis/${analysis.id}/results`}
          className="inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
        >
          View Full Report
          <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    </article>
  );
}

/* ================================================================
   Metric
================================================================ */

function Metric({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs font-medium text-muted">
        {label}
      </p>

      <p className="mt-1 text-xl font-semibold text-slate-900">
        {value}
      </p>
    </div>
  );
}

/* ================================================================
   Helpers
================================================================ */

function getNumber(
  summary: ReportSummary | null,
  field:
    | "total_candidates"
    | "direct_count"
    | "supporting_count"
    | "needs_verification_count",
): number {
  if (!summary) {
    return 0;
  }

  const directValue =
    summary[field];

  if (
    typeof directValue ===
    "number"
  ) {
    return directValue;
  }

  const frontend =
    summary.frontend;

  if (
    frontend &&
    typeof frontend[field] ===
      "number"
  ) {
    return frontend[field];
  }

  return 0;
}

function getCoverage(
  summary: ReportSummary | null,
): number | null {
  if (!summary) {
    return null;
  }

  const directCoverage =
    summary.coverage;

  if (
    directCoverage &&
    typeof directCoverage.coverage_score ===
      "number"
  ) {
    return normalizeCoverage(
      directCoverage.coverage_score,
    );
  }

  const frontendCoverage =
    summary.frontend?.coverage;

  if (
    typeof frontendCoverage ===
    "number"
  ) {
    return normalizeCoverage(
      frontendCoverage,
    );
  }

  if (
    frontendCoverage &&
    typeof frontendCoverage ===
      "object" &&
    "coverage_score" in
      frontendCoverage
  ) {
    const value = Number(
      (
        frontendCoverage as {
          coverage_score?: unknown;
        }
      ).coverage_score,
    );

    if (
      Number.isFinite(value)
    ) {
      return normalizeCoverage(
        value,
      );
    }
  }

  return null;
}

function normalizeCoverage(
  value: number,
): number {
  // Supports either 0–1 or 0–100 representation.
  if (
    value >= 0 &&
    value <= 1
  ) {
    return value * 100;
  }

  return value;
}

function formatCoverage(
  value: number,
): string {
  return `${value.toFixed(0)}%`;
}

function formatDate(
  value?: string,
): string {
  if (!value) {
    return "Date unavailable";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return "Date unavailable";
  }

  return date.toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric",
    },
  );
}