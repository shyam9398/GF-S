export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-medium text-blue-700">
          Configuration
        </p>

        <h1 className="mt-2 text-3xl font-semibold text-ink">
          Settings
        </h1>

        <p className="mt-2 text-sm text-muted">
          Configure application and procurement analysis preferences.
        </p>
      </div>

      <div className="rounded-xl border border-line bg-white p-6 shadow-soft">
        <h2 className="text-base font-semibold text-slate-900">
          Analysis Settings
        </h2>

        <div className="mt-5 space-y-4">
          <div>
            <p className="text-sm font-medium text-slate-700">
              Evidence verification
            </p>

            <p className="mt-1 text-sm text-muted">
              Recommendations should be supported by retrieved BIS evidence.
            </p>
          </div>

          <div>
            <p className="text-sm font-medium text-slate-700">
              Language
            </p>

            <p className="mt-1 text-sm text-muted">
              English
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}