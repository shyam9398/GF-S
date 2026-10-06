import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileText,
  Loader2,
  Upload,
  X,
} from "lucide-react";

import { createAnalysis } from "../services/analysisService";
import { API_BASE_URL } from "../services/api";

const API_URL = API_BASE_URL;

export default function NewAnalysis() {
  const navigate = useNavigate();

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [form, setForm] = useState({
    product_name: "",
    description: "",
    procurement_purpose: "",
    intended_application: "",
    material: "",
    technical_specifications: "",
    performance_requirements: "",
    safety_requirements: "",
    quantity: "",
  });

  function update(
    field: keyof typeof form,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    setError("");

    const file =
      event.target.files?.[0];

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError(
        "Only PDF documents are supported.",
      );

      event.target.value = "";
      setSelectedFile(null);

      return;
    }

    // Keep the upload reasonably bounded at the UI layer.
    // The backend remains the final authority for validation.
    const maxSize =
      25 * 1024 * 1024;

    if (file.size > maxSize) {
      setError(
        "The PDF must be smaller than 25 MB.",
      );

      event.target.value = "";
      setSelectedFile(null);

      return;
    }

    setSelectedFile(file);
  }

  function removeFile() {
    setSelectedFile(null);
  }

  async function uploadDocument(
    analysisId: string,
    file: File,
  ) {
    const formData = new FormData();

    formData.append(
      "file",
      file,
    );

    const response = await fetch(
      `${API_URL}/documents/${analysisId}/upload`,
      {
        method: "POST",
        body: formData,
      },
    );

    let result: unknown = null;

    try {
      result = await response.json();
    } catch {
      result = null;
    }

    if (!response.ok) {
      const body =
        result as {
          detail?: unknown;
          message?: string;
        } | null;

      let message =
        "Unable to upload the PDF.";

      if (
        typeof body?.detail ===
        "string"
      ) {
        message = body.detail;
      } else if (
        body?.detail &&
        typeof body.detail ===
          "object" &&
        "message" in body.detail
      ) {
        message = String(
          (
            body.detail as {
              message: unknown;
            }
          ).message,
        );
      } else if (
        typeof body?.message ===
        "string"
      ) {
        message = body.message;
      }

      throw new Error(message);
    }

    return result;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");

    if (
      !form.product_name.trim() ||
      !form.description.trim()
    ) {
      setError(
        "Product / Service Name and Product Description are required.",
      );

      return;
    }

    if (
      form.quantity &&
      (
        Number.isNaN(
          Number(form.quantity),
        ) ||
        Number(form.quantity) < 1
      )
    ) {
      setError(
        "Quantity must be a valid number greater than 0.",
      );

      return;
    }

    try {
      setLoading(true);

      // --------------------------------------------------------------
      // 1. Create procurement analysis
      // --------------------------------------------------------------

      const analysis =
        await createAnalysis({
          product_name:
            form.product_name.trim(),

          description:
            form.description.trim(),

          procurement_purpose:
            form.procurement_purpose.trim() ||
            undefined,

          intended_application:
            form.intended_application.trim() ||
            undefined,

          material:
            form.material.trim() ||
            undefined,

          technical_specifications:
            form.technical_specifications.trim() ||
            undefined,

          performance_requirements:
            form.performance_requirements.trim() ||
            undefined,

          safety_requirements:
            form.safety_requirements.trim() ||
            undefined,

          quantity: form.quantity
            ? Number(form.quantity)
            : undefined,
        });

      // --------------------------------------------------------------
      // 2. Upload PDF if selected
      // --------------------------------------------------------------

      if (selectedFile) {
        await uploadDocument(
          analysis.id,
          selectedFile,
        );
      }

      // --------------------------------------------------------------
      // 3. Start pipeline through Progress page
      // --------------------------------------------------------------

      navigate(
        `/analysis/${analysis.id}/progress`,
      );
    } catch (error) {
      console.error(
        "Failed to create analysis:",
        error,
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to create the analysis. Make sure the FastAPI backend is running on port 8000.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl">
      {/* ----------------------------------------------------------
          Header
      ---------------------------------------------------------- */}

      <div>
        <button
          type="button"
          onClick={() =>
            navigate("/dashboard")
          }
          disabled={loading}
          className="mb-5 inline-flex items-center gap-2 text-sm font-medium text-muted hover:text-ink disabled:cursor-not-allowed disabled:opacity-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </button>

        <p className="text-sm font-medium text-blue-700">
          New Analysis
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink">
          Procurement Specification
        </h1>

        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
          Provide the available product and technical
          requirements. The system will structure the
          specification, retrieve relevant BIS evidence,
          and identify applicable Indian Standards.
        </p>
      </div>

      {/* ----------------------------------------------------------
          Form
      ---------------------------------------------------------- */}

      <form
        onSubmit={handleSubmit}
        className="mt-8 space-y-6"
      >
        {/* Error */}

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4">
            <p className="text-sm font-medium text-red-800">
              Unable to create analysis
            </p>

            <p className="mt-1 text-sm text-red-700">
              {error}
            </p>
          </div>
        )}

        {/* --------------------------------------------------------
            Basic Requirement
        -------------------------------------------------------- */}

        <section className="rounded-xl border border-line bg-white p-6 shadow-soft">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Basic Requirement
            </h2>

            <p className="mt-1 text-sm text-muted">
              Provide the basic details of the product or
              service being procured.
            </p>
          </div>

          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <Input
              label="Product / Service Name"
              value={form.product_name}
              onChange={(value) =>
                update(
                  "product_name",
                  value,
                )
              }
              required
            />

            <Input
              label="Quantity"
              type="number"
              min="1"
              value={form.quantity}
              onChange={(value) =>
                update(
                  "quantity",
                  value,
                )
              }
            />

            <Input
              label="Intended Application"
              value={
                form.intended_application
              }
              onChange={(value) =>
                update(
                  "intended_application",
                  value,
                )
              }
            />

            <Input
              label="Material"
              value={form.material}
              onChange={(value) =>
                update(
                  "material",
                  value,
                )
              }
            />

            <div className="md:col-span-2">
              <TextArea
                label="Procurement Purpose"
                value={
                  form.procurement_purpose
                }
                onChange={(value) =>
                  update(
                    "procurement_purpose",
                    value,
                  )
                }
                placeholder="Explain why this product or service is being procured."
              />
            </div>
          </div>
        </section>

        {/* --------------------------------------------------------
            Technical Requirements
        -------------------------------------------------------- */}

        <section className="rounded-xl border border-line bg-white p-6 shadow-soft">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Technical Requirements
            </h2>

            <p className="mt-1 text-sm text-muted">
              Add the technical, performance, and safety
              requirements available in the procurement
              specification.
            </p>
          </div>

          <div className="mt-5 space-y-5">
            <TextArea
              label="Product Description"
              value={form.description}
              onChange={(value) =>
                update(
                  "description",
                  value,
                )
              }
              required
              placeholder="Describe what is being procured, its purpose, and how it will be used."
            />

            <TextArea
              label="Technical Specifications"
              value={
                form.technical_specifications
              }
              onChange={(value) =>
                update(
                  "technical_specifications",
                  value,
                )
              }
              placeholder="Dimensions, ratings, capacity, electrical requirements, mechanical requirements, operating conditions, etc."
            />

            <TextArea
              label="Performance Requirements"
              value={
                form.performance_requirements
              }
              onChange={(value) =>
                update(
                  "performance_requirements",
                  value,
                )
              }
              placeholder="Performance levels, durability, efficiency, load capacity, accuracy, service life, etc."
            />

            <TextArea
              label="Safety Requirements"
              value={
                form.safety_requirements
              }
              onChange={(value) =>
                update(
                  "safety_requirements",
                  value,
                )
              }
              placeholder="Safety requirements, protection requirements, hazards, testing requirements, etc."
            />
          </div>
        </section>

        {/* --------------------------------------------------------
            Supporting Document
        -------------------------------------------------------- */}

        <section className="rounded-xl border border-line bg-white p-6 shadow-soft">
          <div>
            <h2 className="text-base font-semibold text-slate-900">
              Supporting Document
            </h2>

            <p className="mt-1 text-sm text-muted">
              Upload a tender, technical specification,
              or procurement document when available.
            </p>
          </div>

          <div className="mt-5">
            {!selectedFile ? (
              <label className="group flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center transition hover:border-blue-400 hover:bg-blue-50/40">
                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white shadow-sm">
                  <Upload className="h-5 w-5 text-brand" />
                </div>

                <p className="mt-4 text-sm font-semibold text-slate-800">
                  Upload procurement PDF
                </p>

                <p className="mt-1 text-sm text-muted">
                  Tender, technical specification, or
                  procurement document
                </p>

                <p className="mt-2 text-xs text-slate-400">
                  PDF only • Maximum 25 MB
                </p>

                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  onChange={
                    handleFileChange
                  }
                  disabled={loading}
                  className="hidden"
                />
              </label>
            ) : (
              <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-white">
                    <FileText className="h-5 w-5 text-brand" />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800">
                      {selectedFile.name}
                    </p>

                    <p className="mt-1 text-xs text-muted">
                      {formatFileSize(
                        selectedFile.size,
                      )}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={
                      removeFile
                    }
                    disabled={loading}
                    className="rounded-lg p-2 text-slate-500 hover:bg-white hover:text-red-600 disabled:opacity-50"
                    aria-label="Remove PDF"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* --------------------------------------------------------
            Submit
        -------------------------------------------------------- */}

        <div className="flex items-center justify-between gap-4">
          <button
            type="button"
            onClick={() =>
              navigate("/dashboard")
            }
            disabled={loading}
            className="rounded-lg border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg bg-brand px-6 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}

            {loading
              ? selectedFile
                ? "Creating & Uploading..."
                : "Creating Analysis..."
              : "Start Analysis"}
          </button>
        </div>
      </form>
    </div>
  );
}

/* --------------------------------------------------
   Input Component
-------------------------------------------------- */

function Input({
  label,
  value,
  onChange,
  type = "text",
  min,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  min?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">
        {label}

        {required && (
          <span className="ml-1 text-red-500">
            *
          </span>
        )}
      </span>

      <input
        type={type}
        min={min}
        value={value}
        required={required}
        onChange={(event) =>
          onChange(
            event.target.value,
          )
        }
        className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </label>
  );
}

/* --------------------------------------------------
   TextArea Component
-------------------------------------------------- */

function TextArea({
  label,
  value,
  onChange,
  placeholder,
  required = false,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-slate-700">
        {label}

        {required && (
          <span className="ml-1 text-red-500">
            *
          </span>
        )}
      </span>

      <textarea
        value={value}
        required={required}
        onChange={(event) =>
          onChange(
            event.target.value,
          )
        }
        placeholder={placeholder}
        className="mt-2 min-h-28 w-full resize-y rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </label>
  );
}

/* --------------------------------------------------
   Helpers
-------------------------------------------------- */

function formatFileSize(
  bytes: number,
) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(
      bytes / 1024
    ).toFixed(1)} KB`;
  }

  return `${(
    bytes /
    (1024 * 1024)
  ).toFixed(1)} MB`;
}