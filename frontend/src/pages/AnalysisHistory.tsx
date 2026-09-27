import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileText,
  Loader2,
  Plus,
} from "lucide-react";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8001/api";

type Analysis = {
  id: string;
  product_name: string;
  description: string;
  procurement_purpose?: string | null;
  intended_application?: string | null;
  material?: string | null;
  quantity?: number | null;
  status: string;
  created_at?: string | null;
  updated_at?: string | null;
};

function formatDate(value?: string | null) {
  if (!value) {
    return "Date unavailable";
  }

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

function formatStatus(status: string) {
  return status
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    );
}

function getStatusStyle(status: string) {
  switch (status.toUpperCase()) {
    case "COMPLETED":
      return "border-emerald-200 bg-emerald-50 text-emerald-700";

    case "PROCESSING":
      return "border-blue-200 bg-blue-50 text-blue-700";

    case "FAILED":
      return "border-red-200 bg-red-50 text-red-700";

    default:
      return "border-slate-200 bg-slate-50 text-slate-600";
  }
}

export default function AnalysisHistory() {
  const [analyses, setAnalyses] = useState<
    Analysis[]
  >([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadAnalyses() {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(
          `${API_URL}/analyses`,
        );

        if (!response.ok) {
          let message =
            "Unable to load analysis history.";

          try {
            const body =
              await response.json();

            if (
              typeof body?.detail ===
              "string"
            ) {
              message = body.detail;
            }
          } catch {
            // Keep default message.
          }

          throw new Error(message);
        }

        const result =
          await response.json();

        /*
         * Support both:
         *
         * [
         *   {...}
         * ]
         *
         * and:
         *
         * {
         *   "items": [...]
         * }
         *
         * This makes the frontend tolerant of the current
         * backend response shape.
         */

        const items = Array.isArray(
          result,
        )
          ? result
          : Array.isArray(result?.items)
            ? result.items
            : Array.isArray(result?.analyses)
              ? result.analyses
              : [];

        if (!cancelled) {
          setAnalyses(items);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : "Unable to load analysis history.",
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadAnalyses();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-medium text-blue-700">
            Workspace
          </p>

          <h1 className="mt-2 text-3xl font-semibold text-ink">
            Analysis History
          </h1>

          <p className="mt-2 text-sm text-muted">
            Review previous procurement specification analyses.
          </p>
        </div>

        <Link
          to="/analysis/new"
          className="inline-flex w-fit items-center gap-2 rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          New Analysis
        </Link>
      </div>

      {/* Loading */}
      {loading && (
        <div className="rounded-xl border border-line bg-white p-10 text-center shadow-soft">
          <Loader2 className="mx-auto h-7 w-7 animate-spin text-brand" />

          <p className="mt-4 text-sm font-medium text-slate-800">
            Loading analysis history
          </p>

          <p className="mt-1 text-sm text-muted">
            Retrieving previous analyses from PostgreSQL.
          </p>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />

            <div>
              <h2 className="text-sm font-semibold text-red-800">
                Unable to load history
              </h2>

              <p className="mt-1 text-sm leading-6 text-red-700">
                {error}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Empty */}
      {!loading &&
        !error &&
        analyses.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-soft">
            <FileText className="mx-auto h-8 w-8 text-slate-400" />

            <p className="mt-4 text-sm font-semibold text-slate-900">
              No analyses yet
            </p>

            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
              Create a procurement analysis to identify relevant
              Indian Standards and build an evidence-backed report.
            </p>

            <Link
              to="/analysis/new"
              className="mt-5 inline-flex items-center gap-2 rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Create Analysis
            </Link>
          </div>
        )}

      {/* Analysis list */}
      {!loading &&
        !error &&
        analyses.length > 0 && (
          <div className="space-y-4">
            {analyses.map((analysis) => (
              <article
                key={analysis.id}
                className="rounded-xl border border-line bg-white p-6 shadow-soft transition-shadow hover:shadow-md"
              >
                <div className="flex flex-col justify-between gap-5 lg:flex-row lg:items-start">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${getStatusStyle(
                          analysis.status,
                        )}`}
                      >
                        {analysis.status.toUpperCase() ===
                        "COMPLETED" ? (
                          <CheckCircle2 className="h-3.5 w-3.5" />
                        ) : (
                          <Clock3 className="h-3.5 w-3.5" />
                        )}

                        {formatStatus(
                          analysis.status,
                        )}
                      </span>

                      <span className="text-xs text-muted">
                        ID: {analysis.id}
                      </span>
                    </div>

                    <h2 className="mt-3 text-lg font-semibold text-ink">
                      {analysis.product_name}
                    </h2>

                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted">
                      {analysis.description}
                    </p>

                    <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted">
                      <span className="inline-flex items-center gap-1.5">
                        <CalendarDays className="h-3.5 w-3.5" />
                        {formatDate(
                          analysis.created_at,
                        )}
                      </span>

                      {analysis.quantity != null && (
                        <span>
                          Quantity: {analysis.quantity}
                        </span>
                      )}

                      {analysis.intended_application && (
                        <span>
                          Application:{" "}
                          {
                            analysis.intended_application
                          }
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="shrink-0">
                    {analysis.status.toUpperCase() ===
                    "COMPLETED" ? (
                      <Link
                        to={`/analysis/${analysis.id}/results`}
                        className="inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
                      >
                        View Results
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    ) : (
                      <Link
                        to={`/analysis/${analysis.id}/progress`}
                        className="inline-flex items-center gap-2 rounded-lg border border-line bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Open Analysis
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
    </div>
  );
}