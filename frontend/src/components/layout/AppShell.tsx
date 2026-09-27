import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import {
  FileSearch,
  LayoutDashboard,
  Plus,
  History,
  FileText,
  Settings,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "New Analysis",
    path: "/analysis/new",
    icon: Plus,
  },
  {
    name: "Analysis History",
    path: "/history",
    icon: History,
  },
  {
    name: "Reports",
    path: "/reports",
    icon: FileText,
  },
  {
    name: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({
  children,
}: AppShellProps) {
  return (
    <div className="min-h-screen bg-surface">

      {/* Sidebar */}

      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white lg:block">

        {/* Logo */}

        <div className="flex h-16 items-center gap-3 border-b border-line px-6">

          <div className="grid h-9 w-9 place-items-center rounded-xl bg-brand text-white">
            <FileSearch size={18} />
          </div>

          <div>
            <p className="text-sm font-semibold text-ink">
              Standards
            </p>

            <p className="text-xs text-muted">
              Intelligence
            </p>
          </div>

        </div>

        {/* Navigation */}

        <nav className="space-y-1 p-4">

          {navigation.map((item) => {

            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  [
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                    isActive
                      ? "bg-blue-50 text-blue-700 font-medium"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                  ].join(" ")
                }
              >

                <Icon size={18} />

                {item.name}

              </NavLink>
            );

          })}

        </nav>

      </aside>

      {/* Main */}

      <main className="min-h-screen lg:pl-64">

        {/* Header */}

        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-line bg-white/95 px-6 backdrop-blur">

          <div>
            <p className="text-sm font-semibold text-ink">
              Indian Standards Recommendation Engine
            </p>

            <p className="text-xs text-muted">
              Procurement intelligence
            </p>
          </div>

          <div className="h-8 w-8 rounded-full bg-slate-200" />

        </header>

        {/* Page */}

        <div className="mx-auto max-w-7xl p-6 lg:p-8">
          {children}
        </div>

      </main>

    </div>
  );
}