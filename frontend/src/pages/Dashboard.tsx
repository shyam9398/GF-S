import { Link } from "react-router-dom";

export default function Dashboard() {
  return (
    <div className="space-y-8">

      {/* Hero */}

      <section className="flex flex-col justify-between gap-6 md:flex-row md:items-end">

        <div>

          <p className="text-sm font-medium text-blue-700">
            Procurement intelligence
          </p>

          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink">
            Find the standards your specification needs.
          </h1>

          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
            Analyze a procurement specification and identify
            relevant Indian Standards with traceable evidence.
          </p>

        </div>

        <Link
          to="/analysis/new"
          className="inline-flex w-fit items-center rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          New Analysis
        </Link>

      </section>

      {/* Empty-state sections */}

      <section className="grid gap-5 md:grid-cols-3">

        <DashboardSection
          title="Recent Analyses"
          description="Your procurement analyses will appear here."
        />

        <DashboardSection
          title="Verification Required"
          description="Recommendations requiring additional verification will appear here."
        />

        <DashboardSection
          title="Reports"
          description="Generated procurement reports will appear here."
        />

      </section>

    </div>
  );
}

function DashboardSection({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-white p-5 shadow-soft">

      <h2 className="text-sm font-semibold text-slate-900">
        {title}
      </h2>

      <p className="mt-2 text-sm leading-6 text-muted">
        {description}
      </p>

    </div>
  );
}