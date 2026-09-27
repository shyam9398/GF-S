import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  FileCheck2,
  FileText,
  FlaskConical,
  GitBranch,
  Loader2,
  ShieldCheck,
  TestTube2,
  TriangleAlert,
} from "lucide-react";

type StandardResult = {
  standard_number: string | null;
  standard_name: string | null;
  classification: string;
  recommendation_level: string;
  applicability_signal: number | null;
  lexical_match: number | null;
  verification_required: boolean;
  reasons: string[];
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
  success: boolean;
  standards: StandardResult[];
  summary: Record<string, number>;
  evidence_graph?: {
    nodes?: unknown[];
    edges?: unknown[];
  };
  coverage?: {
    candidate_count?: number;
    classification_counts?: Record<string, number>;
  };
  disclaimer?: string;
};

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8001/api";

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

function classificationStyle(classification: string) {
  switch (classification) {
    case "DIRECTLY_APPLICABLE":
      return {
        container:
          "border-emerald-200 bg-emerald-50 text-emerald-700",
        icon: CheckCircle2,
      };

    case "RELATED_SUPPORTING":
      return {
        container:
          "border-blue-200 bg-blue-50 text-blue-700",
        icon: GitBranch,
      };

    case "TEST_METHOD":
      return {
        container:
          "border-violet-200 bg-violet-50 text-violet-700",
        icon: TestTube2,
      };

    case "SAMPLING_METHOD":
      return {
        container:
          "border-indigo-200 bg-indigo-50 text-indigo-700",
        icon: FlaskConical,
      };

    case "SAFETY_RELATED":
      return {
        container:
          "border-orange-200 bg-orange-50 text-orange-700",
        icon: ShieldCheck,
      };

    case "NORMATIVE_REFERENCE":
      return {
        container:
          "border-cyan-200 bg-cyan-50 text-cyan-700",
        icon: FileCheck2,
      };

    case "NEEDS_VERIFICATION":
      return {
        container:
          "border-amber-200 bg-amber-50 text-amber-700",
        icon: TriangleAlert,
      };

    default:
      return {
        container:
          "border-slate-200 bg-slate-50 text-slate-700",
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

  const [data, setData] = useState<ResultsResponse | null>(
    null,
  );

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(
    null,
  );

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
          let message =
            "Unable to load analysis results.";

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

        const result =
          (await response.json()) as ResultsResponse;

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
            Retrieving BIS evidence and recommendation results.
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

        <div className="rounded-xl border border-red-200 bg-red-50 p-8">
          <div className="flex items-start gap-3">
            <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />

            <div>
              <h2 className="font-semibold text-red-800">
                Results are not available
              </h2>

              <p className="mt-1 text-sm text-red-700">
                {error ||
                  "No analysis result was returned by the backend."}
              </p>

              <p className="mt-3 text-xs text-red-600">
                The analysis may not have been started yet, or the
                backend may still be processing it.
              </p>
            </div>
          </div>
        </div>

        <Link
          to={`/analysis/${id}/progress`}
          className="inline-flex rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          Open Analysis Progress
        </Link>
      </div>
    );
  }

  const standards = data.standards || [];

  const summary = data.summary || {};

  const directCount =
    summary["direct"] || 0;

  const supportingCount =
    summary["supporting"] || 0;

  const testMethodCount =
    summary["test_methods"] || 0;

  const verificationCount =
    summary["needs_verification"] || 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <Link
            to={`/analysis/${id}/progress`}
            className="mb-4 inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink"
          >
            <ArrowLeft className="h-4 w-4" />
            Analysis Progress
          </Link>

          <p className="text-sm font-medium text-blue-700">
            Analysis Results
          </p>

          <h1 className="mt-2 text-3xl font-semibold text-ink">
            Indian Standards Evidence Report
          </h1>

          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
            Standards identified from the procurement requirements,
            enriched with information retrieved from BIS and evaluated
            for their relationship to the procurement.
          </p>

          <p className="mt-2 text-xs text-muted">
            Analysis ID: {id}
          </p>
        </div>

        <Link
          to="/analysis/new"
          className="inline-flex w-fit rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          New Analysis
        </Link>
      </div>

      {/* Summary */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          label="Total Candidates"
          value={standards.length}
        />

        <SummaryCard
          label="Direct Matches"
          value={directCount}
        />

        <SummaryCard
          label="Supporting"
          value={supportingCount}
        />

        <SummaryCard
          label="Needs Verification"
          value={verificationCount}
        />
      </div>

      {/* Coverage */}
      {data.coverage && (
        <div className="rounded-xl border border-line bg-white p-6 shadow-soft">
          <div className="flex items-start gap-3">
            <FileCheck2 className="mt-0.5 h-5 w-5 text-brand" />

            <div>
              <h2 className="font-semibold text-ink">
                Retrieval Coverage
              </h2>

              <p className="mt-1 text-sm text-muted">
                This shows how much BIS search/evidence retrieval was
                completed. It should not be interpreted as proof that
                every Indian Standard has been considered.
              </p>
            </div>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2">
            <div className="rounded-lg bg-slate-50 p-4">
              <p className="text-xs text-muted">
                Candidate standards
              </p>

              <p className="mt-1 text-xl font-semibold text-ink">
                {data.coverage.candidate_count ?? standards.length}
              </p>
            </div>

            <div className="rounded-lg bg-slate-50 p-4">
              <p className="text-xs text-muted">
                Test method references
              </p>

              <p className="mt-1 text-xl font-semibold text-ink">
                {testMethodCount}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Standards */}
      <div className="space-y-5">
        <div>
          <h2 className="text-xl font-semibold text-ink">
            Standards
          </h2>

          <p className="mt-1 text-sm text-muted">
            Each result includes its applicability signal and available
            BIS evidence.
          </p>
        </div>

        {standards.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-soft">
            <FileText className="mx-auto h-8 w-8 text-slate-400" />

            <h3 className="mt-4 font-semibold text-slate-800">
              No standards were returned
            </h3>

            <p className="mt-2 text-sm text-muted">
              The backend did not return any candidate standards for
              this analysis.
            </p>
          </div>
        ) : (
          standards.map((standard, index) => {
            const style = classificationStyle(
              standard.classification,
            );

            const StatusIcon = style.icon;

            const version =
              standard.version_information || {};

            const conformity =
              standard.conformity || {};

            const evidence =
              standard.evidence_summary || {};

            return (
              <article
                key={`${standard.standard_number}-${index}`}
                className="rounded-xl border border-line bg-white p-6 shadow-soft"
              >
                {/* Standard header */}
                <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-md bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-800">
                        {standard.standard_number ||
                          "Standard number unavailable"}
                      </span>

                      <span
                        className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium ${style.container}`}
                      >
                        <StatusIcon className="h-3.5 w-3.5" />

                        {formatClassification(
                          standard.classification,
                        )}
                      </span>
                    </div>

                    <h3 className="mt-3 text-lg font-semibold text-ink">
                      {standard.standard_name ||
                        "Standard title unavailable"}
                    </h3>

                    <p className="mt-1 text-xs text-muted">
                      {standard.recommendation_level}
                    </p>
                  </div>

                  {standard.verification_required && (
                    <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs font-medium text-amber-800">
                      <TriangleAlert className="h-4 w-4" />
                      Additional verification required
                    </div>
                  )}
                </div>

                {/* Applicability signal */}
                <div className="mt-6 grid gap-4 sm:grid-cols-2">
                  <div className="rounded-lg border border-line p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted">
                      Applicability signal
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-ink">
                      {standard.applicability_signal != null
                        ? `${Math.round(
                            standard.applicability_signal * 100,
                          )}%`
                        : "N/A"}
                    </p>
                  </div>

                  <div className="rounded-lg border border-line p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-muted">
                      Textual match
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-ink">
                      {standard.lexical_match != null
                        ? `${Math.round(
                            standard.lexical_match * 100,
                          )}%`
                        : "N/A"}
                    </p>
                  </div>
                </div>

                {/* Reasons */}
                {standard.reasons.length > 0 && (
                  <div className="mt-6">
                    <h4 className="text-sm font-semibold text-ink">
                      Why this standard was identified
                    </h4>

                    <div className="mt-3 space-y-2">
                      {standard.reasons.map(
                        (reason, reasonIndex) => (
                          <div
                            key={reasonIndex}
                            className="flex gap-2 text-sm leading-6 text-slate-600"
                          >
                            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" />

                            <span>{reason}</span>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {/* Version */}
                <div className="mt-6 border-t border-line pt-6">
                  <h4 className="text-sm font-semibold text-ink">
                    Version and status evidence
                  </h4>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <p className="text-xs text-muted">
                        Published
                      </p>

                      <p className="mt-1 text-sm font-medium text-slate-800">
                        {formatDate(
                          version.published_on,
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-muted">
                        Review
                      </p>

                      <p className="mt-1 text-sm font-medium text-slate-800">
                        {formatDate(
                          version.review_on,
                        )}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-muted">
                        Reaffirmation
                      </p>

                      <p className="mt-1 text-sm font-medium text-slate-800">
                        {version.reaffirmation_year ||
                          "Not available"}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-muted">
                        Amendments
                      </p>

                      <p className="mt-1 text-sm font-medium text-slate-800">
                        {version.amendment_count ??
                          "Not available"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Related standards */}
                {standard.related_standards.length > 0 && (
                  <div className="mt-6 border-t border-line pt-6">
                    <div className="flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-brand" />

                      <h4 className="text-sm font-semibold text-ink">
                        Related BIS references
                      </h4>
                    </div>

                    <div className="mt-4 space-y-2">
                      {standard.related_standards.map(
                        (related, relatedIndex) => (
                          <div
                            key={relatedIndex}
                            className="rounded-lg border border-line bg-slate-50 p-3"
                          >
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-slate-800">
                                {related.standard_number ||
                                  "Standard number unavailable"}
                              </span>

                              {related.relationship_type && (
                                <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600">
                                  {formatClassification(
                                    related.relationship_type,
                                  )}
                                </span>
                              )}
                            </div>

                            {related.standard_name && (
                              <p className="mt-1 text-xs text-muted">
                                {related.standard_name}
                              </p>
                            )}
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {/* Conformity evidence */}
                <div className="mt-6 border-t border-line pt-6">
                  <h4 className="text-sm font-semibold text-ink">
                    BIS conformity evidence
                  </h4>

                  <div className="mt-4 flex flex-wrap gap-2">
                    <EvidenceBadge
                      label={`Licenses: ${
                        conformity.license_records ?? 0
                      }`}
                      available={
                        conformity.license_evidence_available ??
                        false
                      }
                    />

                    <EvidenceBadge
                      label={`CRS: ${
                        conformity.crs_records ?? 0
                      }`}
                      available={
                        conformity.crs_evidence_available ??
                        false
                      }
                    />

                    <EvidenceBadge
                      label={`MCS: ${
                        conformity.mcs_records ?? 0
                      }`}
                      available={
                        conformity.mcs_evidence_available ??
                        false
                      }
                    />

                    <EvidenceBadge
                      label={`Laboratories: ${
                        conformity.laboratory_records ?? 0
                      }`}
                      available={
                        conformity.laboratory_evidence_available ??
                        false
                      }
                    />
                  </div>

                  {conformity.note && (
                    <p className="mt-3 text-xs leading-5 text-muted">
                      {conformity.note}
                    </p>
                  )}
                </div>

                {/* Evidence availability */}
                <div className="mt-6 border-t border-line pt-6">
                  <h4 className="text-sm font-semibold text-ink">
                    Retrieved evidence
                  </h4>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {(evidence.available || []).map(
                      (item) => (
                        <EvidenceBadge
                          key={item}
                          label={formatClassification(
                            item,
                          )}
                          available={true}
                        />
                      ),
                    )}

                    {(evidence.unavailable || []).map(
                      (item) => (
                        <EvidenceBadge
                          key={item}
                          label={formatClassification(
                            item,
                          )}
                          available={false}
                        />
                      ),
                    )}
                  </div>
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
                Important
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