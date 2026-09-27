import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Loader2,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";

const API_URL =
  import.meta.env.VITE_API_URL ||
  "http://localhost:8001/api";

type PipelineStage =
  | "starting"
  | "requirements"
  | "search"
  | "evidence"
  | "recommendation"
  | "completed"
  | "failed";

export default function AnalysisProgress() {
  const { id } = useParams<{ id: string }>();

  const navigate = useNavigate();

  const [stage, setStage] =
    useState<PipelineStage>("starting");

  const [error, setError] =
    useState<string | null>(null);

  const [started, setStarted] =
    useState(false);

  // Prevent duplicate POST requests during React development
  // StrictMode mounting.
  const runStartedRef = useRef(false);

  useEffect(() => {
    if (!id) {
      setError("Analysis ID is missing.");
      setStage("failed");
      return;
    }

    if (runStartedRef.current) {
      return;
    }

    runStartedRef.current = true;

    async function runPipeline() {
      try {
        setStarted(true);
        setError(null);

        // ------------------------------------------------------------
        // Stage 1
        // ------------------------------------------------------------

        setStage("requirements");

        // Give the UI a moment to show the first stage before the
        // potentially long backend request starts.
        await wait(300);

        // ------------------------------------------------------------
        // Stage 2
        // ------------------------------------------------------------

        setStage("search");

        const response = await fetch(
          `${API_URL}/analyses/${id}/run`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          },
        );

        // ------------------------------------------------------------
        // Read response
        // ------------------------------------------------------------

        let result: any = null;

        try {
          result = await response.json();
        } catch {
          result = null;
        }

        if (!response.ok) {
          const message =
            result?.detail?.error ||
            result?.detail?.message ||
            result?.detail ||
            result?.error ||
            "The analysis pipeline failed.";

          throw new Error(
            typeof message === "string"
              ? message
              : "The analysis pipeline failed.",
          );
        }

        if (!result?.success) {
          throw new Error(
            result?.error ||
              "The analysis pipeline did not complete successfully.",
          );
        }

        // ------------------------------------------------------------
        // The backend currently executes the complete BIS pipeline
        // inside this request. These stages are therefore visual
        // progress indicators rather than separate backend jobs.
        // ------------------------------------------------------------

        setStage("evidence");

        await wait(500);

        setStage("recommendation");

        await wait(500);

        setStage("completed");

        await wait(700);

        // ------------------------------------------------------------
        // Redirect to results
        // ------------------------------------------------------------

        navigate(
          `/analysis/${id}/results`,
          {
            replace: true,
          },
        );
      } catch (err) {
        setStage("failed");

        setError(
          err instanceof Error
            ? err.message
            : "Unable to run the analysis.",
        );
      }
    }

    runPipeline();
  }, [id, navigate]);

  const currentStageIndex =
    getStageIndex(stage);

  return (
    <div className="space-y-6">
      {/* Back */}
      <div>
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>

      {/* Header */}
      <div>
        <p className="text-sm font-medium text-blue-700">
          Analysis
        </p>

        <h1 className="mt-2 text-3xl font-semibold text-ink">
          {stage === "completed"
            ? "Analysis completed"
            : stage === "failed"
              ? "Analysis could not be completed"
              : "Analysis in progress"}
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          The system is analyzing your procurement specification,
          retrieving evidence from BIS, and preparing the
          standards recommendation.
        </p>

        <p className="mt-2 text-xs text-muted">
          Analysis ID: {id}
        </p>
      </div>

      {/* Main progress card */}
      <div className="rounded-xl border border-line bg-white p-6 shadow-soft">
        {/* Current status */}
        <div className="flex items-start gap-4">
          <StatusIcon stage={stage} />

          <div className="min-w-0">
            <p className="font-medium text-slate-900">
              {getStageTitle(stage)}
            </p>

            <p className="mt-1 text-sm text-muted">
              {getStageDescription(stage)}
            </p>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-7">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-600">
              Pipeline progress
            </span>

            <span className="font-medium text-slate-600">
              {stage === "failed"
                ? "Failed"
                : `${Math.round(
                    (currentStageIndex /
                      PIPELINE_STAGES.length) *
                      100,
                  )}%`}
            </span>
          </div>

          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className={[
                "h-full rounded-full transition-all duration-500",
                stage === "failed"
                  ? "bg-red-500"
                  : "bg-brand",
              ].join(" ")}
              style={{
                width:
                  stage === "failed"
                    ? "100%"
                    : `${Math.max(
                        8,
                        Math.min(
                          100,
                          (currentStageIndex /
                            PIPELINE_STAGES.length) *
                            100,
                        ),
                      )}%`,
              }}
            />
          </div>
        </div>

        {/* Pipeline stages */}
        <div className="mt-8 space-y-1">
          <ProgressItem
            icon={Sparkles}
            title="Specification understanding"
            description="Understanding the product, application, technical, performance, and safety requirements."
            state={getItemState(
              "requirements",
              stage,
            )}
          />

          <ProgressItem
            icon={Search}
            title="BIS standards retrieval"
            description="Searching BIS dynamically using multiple procurement search concepts."
            state={getItemState(
              "search",
              stage,
            )}
          />

          <ProgressItem
            icon={ShieldCheck}
            title="Evidence enrichment"
            description="Retrieving BIS details, amendments, references, certification and related evidence."
            state={getItemState(
              "evidence",
              stage,
            )}
          />

          <ProgressItem
            icon={CheckCircle2}
            title="Recommendation generation"
            description="Evaluating applicability and preparing the evidence-backed procurement report."
            state={getItemState(
              "recommendation",
              stage,
            )}
          />
        </div>

        {/* Error */}
        {stage === "failed" && (
          <div className="mt-7 rounded-lg border border-red-200 bg-red-50 p-4">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" />

              <div>
                <p className="text-sm font-semibold text-red-800">
                  Analysis failed
                </p>

                <p className="mt-1 text-sm leading-6 text-red-700">
                  {error ||
                    "An unexpected error occurred while processing the analysis."}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Success */}
        {stage === "completed" && (
          <div className="mt-7 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />

              <div>
                <p className="text-sm font-semibold text-emerald-800">
                  Analysis completed successfully
                </p>

                <p className="mt-1 text-sm leading-6 text-emerald-700">
                  The recommendation report and BIS evidence are
                  ready to review.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="mt-8 flex flex-wrap gap-3">
          {stage === "completed" && (
            <Link
              to={`/analysis/${id}/results`}
              className="inline-flex rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
            >
              View Results
            </Link>
          )}

          {stage === "failed" && (
            <button
              type="button"
              onClick={() => {
                window.location.reload();
              }}
              className="inline-flex rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
            >
              Try Again
            </button>
          )}

          <Link
            to="/analysis/new"
            className="inline-flex rounded-lg border border-line bg-white px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            New Analysis
          </Link>
        </div>

        {/* Technical note */}
        {started &&
          stage !== "failed" &&
          stage !== "completed" && (
            <p className="mt-6 text-xs leading-5 text-muted">
              BIS retrieval may take some time because the system
              performs dynamic searches and gathers evidence from
              multiple BIS data sources.
            </p>
          )}
      </div>
    </div>
  );
}

const PIPELINE_STAGES: PipelineStage[] = [
  "requirements",
  "search",
  "evidence",
  "recommendation",
  "completed",
];

function wait(milliseconds: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(
      resolve,
      milliseconds,
    );
  });
}

function getStageIndex(
  stage: PipelineStage,
) {
  if (stage === "starting") {
    return 0;
  }

  if (stage === "failed") {
    return 0;
  }

  const index =
    PIPELINE_STAGES.indexOf(stage);

  return index >= 0 ? index + 1 : 0;
}

function getStageTitle(
  stage: PipelineStage,
) {
  switch (stage) {
    case "starting":
      return "Starting analysis";

    case "requirements":
      return "Understanding procurement requirements";

    case "search":
      return "Searching BIS standards";

    case "evidence":
      return "Collecting BIS evidence";

    case "recommendation":
      return "Generating recommendations";

    case "completed":
      return "Recommendation report ready";

    case "failed":
      return "Pipeline execution failed";

    default:
      return "Processing analysis";
  }
}

function getStageDescription(
  stage: PipelineStage,
) {
  switch (stage) {
    case "starting":
      return "Preparing the analysis pipeline.";

    case "requirements":
      return "Gemini is structuring the procurement requirements into searchable concepts.";

    case "search":
      return "The backend is dynamically searching BIS for candidate Indian Standards.";

    case "evidence":
      return "The backend is retrieving standard details, amendments, relationships, and conformity evidence.";

    case "recommendation":
      return "The applicability and evidence layers are being converted into a procurement report.";

    case "completed":
      return "The analysis has completed and the results are ready.";

    case "failed":
      return "The backend returned an error while processing this analysis.";

    default:
      return "Processing analysis.";
  }
}

function getItemState(
  itemStage: PipelineStage,
  currentStage: PipelineStage,
): "completed" | "active" | "pending" | "failed" {
  if (currentStage === "failed") {
    return "failed";
  }

  if (currentStage === "completed") {
    return "completed";
  }

  const currentIndex =
    PIPELINE_STAGES.indexOf(
      currentStage,
    );

  const itemIndex =
    PIPELINE_STAGES.indexOf(
      itemStage,
    );

  if (itemIndex < currentIndex) {
    return "completed";
  }

  if (itemIndex === currentIndex) {
    return "active";
  }

  return "pending";
}

function StatusIcon({
  stage,
}: {
  stage: PipelineStage;
}) {
  if (stage === "failed") {
    return (
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-50">
        <AlertCircle className="h-5 w-5 text-red-600" />
      </div>
    );
  }

  if (stage === "completed") {
    return (
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50">
        <CheckCircle2 className="h-5 w-5 text-emerald-600" />
      </div>
    );
  }

  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-50">
      <Loader2 className="h-5 w-5 animate-spin text-brand" />
    </div>
  );
}

function ProgressItem({
  icon: Icon,
  title,
  description,
  state,
}: {
  icon: typeof Sparkles;
  title: string;
  description: string;
  state:
    | "completed"
    | "active"
    | "pending"
    | "failed";
}) {
  const stateStyles = {
    completed:
      "border-emerald-500 bg-emerald-500 text-white",

    active:
      "border-brand bg-blue-50 text-brand",

    pending:
      "border-slate-300 bg-white text-slate-400",

    failed:
      "border-red-500 bg-red-50 text-red-600",
  };

  return (
    <div className="flex gap-4 rounded-lg p-3">
      <div
        className={[
          "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border",
          stateStyles[state],
        ].join(" ")}
      >
        {state === "completed" ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : state === "active" ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : state === "failed" ? (
          <AlertCircle className="h-4 w-4" />
        ) : (
          <Icon className="h-4 w-4" />
        )}
      </div>

      <div className="min-w-0 pt-0.5">
        <p
          className={[
            "text-sm font-medium",
            state === "pending"
              ? "text-slate-500"
              : "text-slate-900",
          ].join(" ")}
        >
          {title}
        </p>

        <p className="mt-1 text-sm leading-6 text-muted">
          {description}
        </p>
      </div>
    </div>
  );
}