import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="grid min-h-[60vh] place-items-center">
      <div className="text-center">
        <p className="text-sm font-medium text-blue-700">
          404
        </p>

        <h1 className="mt-2 text-3xl font-semibold text-ink">
          Page not found
        </h1>

        <p className="mt-3 text-sm text-muted">
          The page you are looking for does not exist.
        </p>

        <Link
          to="/dashboard"
          className="mt-6 inline-flex rounded-lg bg-brand px-5 py-3 text-sm font-medium text-white hover:bg-blue-700"
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}