import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  FileSearch,
  FileText,
  Layers,
  Loader2,
  Scale,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";

import { API_BASE_URL } from "../services/api";

const API_URL = API_BASE_URL;

export type PipelineStage =
  | "uploading"
  | "extracting"
  | "understanding"
  | "bis_search"
  | "ranking"
  | "validating"
  | "preparing_evidence"
  | "completed"
  | "failed";

const PIPELINE_STAGES: {
  key: PipelineStage;
  title: string;
  description: string;
  icon: any;
}[] = [
  {
    key: "uploading",
    title: "Uploading",
    description: "Document uploaded and procurement parameters validated.",
    icon: Upload,
  },
  {
    key: "extracting",
    title: "Extracting Document",
    description: "Extracting structured specifications, tables, and sections using Docling.",
    icon: FileSearch,
  },
  {
    key: "understanding",
    title: "Understanding Specifications",
    description: "Semantic analysis extracting materials, technical requirements, parameters, and safety requirements.",
    icon: Sparkles,
  },
  {
    key: "bis_search",
    title: "Searching BIS Standards",
    description: "Dynamically retrieving candidate Indian Standards from official BIS endpoints.",
    icon: Search,
  },
  {
    key: "ranking",
    title: "Ranking Standards",
    description: "Deterministic scoring across product, application, technical, material, and safety dimensions.",
    icon: Scale,
  },
  {
    key: "validating",
    title: "Validating Applicability",
    description: "Cross-validating standard status, versions, amendments, and scope applicability.",
    icon: Layers,
  },
  {
    key: "preparing_evidence",
    title: "Preparing Evidence",
    description: "Compiling BIS citations, certification licenses, and laboratory testing references.",
    icon: ShieldCheck,
  },
  {
    key: "completed",
    title: "Analysis Complete",
    description: "Evidence-backed recommendation report ready to review.",
    icon: CheckCircle2,
  },
];

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export default function AnalysisProgress() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [stage, setStage] = useState<PipelineStage>("uploading");
  const [failedStageName, setFailedStageName] = useState<string>("Analysis Pipeline");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [started, setStarted] = useState(false);

  const runStartedRef = useRef(false);

  useEffect(() => {
    if (!id) {
      setErrorMessage("Analysis ID is missing.");
      setFailedStageName("Initialization");
      setStage("failed");
      return;
    }

    if (runStartedRef.current) {
      return;
    }

    runStartedRef.current = true;

    async function runPipeline() {
      setStarted(true);
      setErrorMessage(null);

      // Progressive stage transitions while the backend request runs
      let currentStage: PipelineStage = "uploading";
      const timer1 = setTimeout(() => {
        if (currentStage === "uploading") {
          currentStage = "extracting";
          setStage("extracting");
        }
      }, 800);

      const timer2 = setTimeout(() => {
        if (currentStage === "extracting") {
          currentStage = "understanding";
          setStage("understanding");
        }
      }, 2500);

      const timer3 = setTimeout(() => {
        if (currentStage === "understanding") {
          currentStage = "bis_search";
          setStage("bis_search");
        }
      }, 7000);

      const timer4 = setTimeout(() => {
        if (currentStage === "bis_search") {
          currentStage = "ranking";
          setStage("ranking");
        }
      }, 15000);

      try {
        const response = await fetch(`${API_URL}/analyses/${id}/run`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });

        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);

        let result: any = null;
        try {
          result = await response.json();
        } catch {
          result = null;
        }

        if (!response.ok) {
          const detail = result?.detail || result;
          const stageName = detail?.stage || detail?.errors?.[0]?.stage || currentStage;
          const msg =
            detail?.error ||
            detail?.message ||
            detail?.errors?.[0]?.message ||
            (typeof detail === "string" ? detail : "The analysis pipeline failed.");

          setFailedStageName(formatStageTitle(stageName));
          setErrorMessage(msg);
          setStage("failed");
          return;
        }

        if (result?.status === "failed" || result?.success === false) {
          const stageName = result?.stage || result?.errors?.[0]?.stage || currentStage;
          const msg =
            result?.error ||
            result?.errors?.[0]?.message ||
            "The analysis pipeline encountered an error.";

          setFailedStageName(formatStageTitle(stageName));
          setErrorMessage(msg);
          setStage("failed");
          return;
        }

        // Advance quickly through remaining visual stages
        setStage("validating");
        await wait(500);
        setStage("preparing_evidence");
        await wait(500);
        setStage("completed");
        await wait(800);

        navigate(`/analysis/${id}/results`, { replace: true });
      } catch (err) {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
        clearTimeout(timer4);

        setFailedStageName(formatStageTitle(currentStage));
        setErrorMessage(
          err instanceof Error
            ? err.message
            : "Network or server connection error while communicating with backend.",
        );
        setStage("failed");
      }
    }

    runPipeline();
  }, [id, navigate]);

  function formatStageTitle(key: string): string {
    const matched = PIPELINE_STAGES.find((s) => s.key === key);
    if (matched) return matched.title;
    return key
      .replaceAll("_", " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  const currentStageIndex = PIPELINE_STAGES.findIndex((s) => s.key === stage);

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
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-700">
          Analysis Pipeline
        </p>

        <h1 className="mt-2 text-3xl font-semibold text-ink">
          {stage === "completed"
            ? "Analysis Complete"
            : stage === "failed"
              ? "Analysis failed"
              : "Analyzing Procurement Specification"}
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          Dynamic multi-stage pipeline: Docling document extraction, semantic requirement structuring,
          live BIS standards retrieval, deterministic scoring, and evidence verification.
        </p>

        <p className="mt-2 text-xs text-muted">Analysis ID: {id}</p>
      </div>

      {/* Main Progress Card */}
      <div className="rounded-xl border border-line bg-white p-6 shadow-soft">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-slate-700">Pipeline Execution Progress</span>
            <span className="font-semibold text-slate-700">
              {stage === "failed"
                ? "Failed"
                : `${Math.round(
                    ((currentStageIndex + 1) / PIPELINE_STAGES.length) * 100,
                  )}%`}
            </span>
          </div>

          <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div
              className={[
                "h-full rounded-full transition-all duration-500",
                stage === "failed" ? "bg-red-500" : "bg-brand",
              ].join(" ")}
              style={{
                width:
                  stage === "failed"
                    ? "100%"
                    : `${Math.max(
                        12,
                        Math.min(
                          100,
                          ((currentStageIndex + 1) / PIPELINE_STAGES.length) * 100,
                        ),
                      )}%`,
              }}
            />
          </div>
        </div>

        {/* 8 Pipeline Stages */}
        <div className="space-y-2">
          {PIPELINE_STAGES.map((s, idx) => {
            const Icon = s.icon;
            const isCompleted =
              stage === "completed" ||
              (stage !== "failed" && idx < currentStageIndex);
            const isActive = stage === s.key;
            const isFailed = stage === "failed" && idx === currentStageIndex;

            return (
              <div
                key={s.key}
                className={[
                  "flex items-start gap-4 rounded-lg p-3 transition-colors",
                  isActive ? "bg-blue-50/70 border border-blue-100" : "",
                ].join(" ")}
              >
                <div
                  className={[
                    "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full border text-sm",
                    isCompleted
                      ? "border-emerald-500 bg-emerald-500 text-white"
                      : isActive
                        ? "border-brand bg-blue-100 text-brand"
                        : isFailed
                          ? "border-red-500 bg-red-100 text-red-600"
                          : "border-slate-200 bg-slate-50 text-slate-400",
                  ].join(" ")}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="h-4 w-4" />
                  ) : isActive ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : isFailed ? (
                    <AlertCircle className="h-4 w-4" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </div>

                <div className="min-w-0 pt-0.5">
                  <p
                    className={[
                      "text-sm font-semibold",
                      isActive
                        ? "text-blue-900"
                        : isCompleted
                          ? "text-slate-800"
                          : isFailed
                            ? "text-red-700"
                            : "text-slate-500",
                    ].join(" ")}
                  >
                    {s.title}
                  </p>
                  <p className="mt-0.5 text-xs text-muted leading-relaxed">
                    {s.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Error Card as specified in Section 19 */}
        {stage === "failed" && (
          <div className="mt-7 rounded-xl border border-red-200 bg-red-50/80 p-5">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-6 w-6 shrink-0 text-red-600" />
              <div>
                <h3 className="text-base font-bold text-red-900">Analysis failed</h3>

                <div className="mt-3 space-y-1.5 text-sm text-red-800">
                  <p>
                    <span className="font-semibold text-red-950">Stage:</span>{" "}
                    {failedStageName}
                  </p>
                  <p>
                    <span className="font-semibold text-red-950">Reason:</span>{" "}
                    {errorMessage || "An unexpected error occurred during execution."}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Success Card */}
        {stage === "completed" && (
          <div className="mt-7 rounded-xl border border-emerald-200 bg-emerald-50/80 p-5">
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-6 w-6 shrink-0 text-emerald-600" />
              <div>
                <h3 className="text-base font-bold text-emerald-900">
                  Analysis Complete
                </h3>
                <p className="mt-1 text-sm text-emerald-800 leading-relaxed">
                  BIS recommendations, applicability scores, revisions, amendments, and conformity evidence
                  are ready.
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
              className="inline-flex rounded-lg bg-red-600 px-5 py-3 text-sm font-medium text-white hover:bg-red-700"
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

        {started && stage !== "failed" && stage !== "completed" && (
          <p className="mt-6 text-xs text-muted">
            The pipeline is communicating live with official BIS standards endpoints and performing semantic analysis.
            Execution takes 15–30 seconds.
          </p>
        )}
      </div>
    </div>
  );
}