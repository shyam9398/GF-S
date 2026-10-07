import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  FileSearch,
  LayoutDashboard,
  Plus,
  History,
  FileText,
  Settings,
  Languages,
  Menu,
  X,
  ExternalLink,
  LogOut,
  Shield,
} from "lucide-react";
import { useTranslation } from "../../i18n/I18nContext";
import { useAuth } from "../../context/AuthContext";

interface AppShellProps {
  children: ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const { t, language, setLanguage, languages, currentLangMeta } = useTranslation();
  const { profile, user, signOut } = useAuth();
  const navigate = useNavigate();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);

  // Derive username with fallback
  const username =
    profile?.username ||
    (user?.user_metadata?.username as string) ||
    user?.email?.replace("@bis.local", "") ||
    "officer.bis";

  const handleLogout = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  const navigation = [
    {
      name: t("nav.dashboard", "Dashboard"),
      path: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: t("nav.new_analysis", "New Analysis"),
      path: "/analysis/new",
      icon: Plus,
    },
    {
      name: t("nav.history", "Analysis History"),
      path: "/history",
      icon: History,
    },
    {
      name: t("nav.reports", "Reports"),
      path: "/reports",
      icon: FileText,
    },
    {
      name: t("nav.settings", "Settings"),
      path: "/settings",
      icon: Settings,
    },
  ];

  return (
    <div className="min-h-screen bg-[#F7F8FA] text-slate-900 font-sans antialiased">
      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar - Desktop & Mobile */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 border-r border-slate-200 bg-white transition-transform duration-200 ease-in-out lg:translate-x-0 flex flex-col ${
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {/* Logo */}
        <div className="flex h-16 items-center justify-between border-b border-slate-200 px-5 shrink-0">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#0F2B48] text-white shadow-sm">
              <FileSearch size={18} />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900 leading-tight">
                {t("brand.title", "Standards")}
              </p>
              <p className="text-xs font-medium text-slate-500">
                {t("brand.subtitle", "Intelligence")}
              </p>
            </div>
          </div>
          <button
            onClick={() => setMobileMenuOpen(false)}
            className="p-1 rounded-md text-slate-400 hover:text-slate-600 lg:hidden"
          >
            <X size={20} />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-3 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  [
                    "flex items-center gap-3 rounded-lg px-3.5 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700 shadow-xs"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                  ].join(" ")
                }
              >
                <Icon size={18} />
                {item.name}
              </NavLink>
            );
          })}
        </nav>

        {/* Procurement Officer Identity & Logout in Sidebar */}
        <div className="p-3 border-t border-slate-200 bg-slate-50 shrink-0">
          <div className="flex items-center gap-2.5 mb-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#0F2B48] text-white flex items-center justify-center font-bold text-xs border border-blue-950 shrink-0 shadow-2xs">
              <Shield size={14} className="text-red-400" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider leading-none">
                Procurement Officer
              </p>
              <p className="text-xs font-bold text-[#0F2B48] truncate mt-1 font-mono" title={username}>
                {username}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-red-700 bg-red-50 hover:bg-red-100/80 border border-red-200 rounded-lg transition cursor-pointer"
          >
            <LogOut size={13} />
            <span>Logout</span>
          </button>
        </div>

        {/* Portal Info Footer */}
        <div className="p-3 border-t border-slate-200 bg-slate-100/60 shrink-0">
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span className="font-semibold text-slate-700">BIS Care Portal</span>
            <a
              href="https://www.services.bis.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 inline-flex items-center gap-1"
            >
              Verify <ExternalLink size={11} />
            </a>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">SIH 2026 Prototype • PS 26108</p>
        </div>
      </aside>

      {/* Main Container */}
      <main className="min-h-screen lg:pl-64 flex flex-col">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-5 lg:px-8 backdrop-blur">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 -ml-2 rounded-lg text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>
            <div>
              <h1 className="text-sm font-semibold text-slate-900 leading-snug">
                {t("header.title", "Indian Standards Recommendation Engine")}
              </h1>
              <p className="text-xs text-slate-500 hidden sm:block">
                {t("header.subtitle", "Procurement intelligence for BIS compliance")}
              </p>
            </div>
          </div>

          {/* Right Header Actions */}
          <div className="flex items-center gap-3">
            {/* Language Selector Dropdown */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setLangDropdownOpen(!langDropdownOpen)}
                className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-2xs hover:bg-slate-50 transition"
              >
                <Languages size={15} className="text-blue-600" />
                <span className="font-semibold">{currentLangMeta.nativeName}</span>
                <span className="text-[10px] text-slate-400 uppercase">({currentLangMeta.code})</span>
              </button>

              {langDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setLangDropdownOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 z-50 w-64 max-h-80 overflow-y-auto rounded-xl border border-slate-200 bg-white p-1.5 shadow-lg">
                    <div className="px-2 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                      Select Language (22+ Indic)
                    </div>
                    {languages.map((lang) => (
                      <button
                        key={lang.code}
                        onClick={() => {
                          setLanguage(lang.code);
                          setLangDropdownOpen(false);
                        }}
                        className={`flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-xs text-left transition ${
                          language === lang.code
                            ? "bg-blue-50 font-semibold text-blue-700"
                            : "text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        <span>{lang.nativeName}</span>
                        <span className="text-[11px] text-slate-400">{lang.name}</span>
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>

            <div className="hidden sm:flex items-center gap-2 pl-2 border-l border-slate-200 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              BIS Live
            </div>

            {/* Officer Profile Badge & Quick Logout in Header */}
            <div className="hidden md:flex items-center gap-2 pl-2 border-l border-slate-200">
              <div className="text-right">
                <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 leading-none">
                  Procurement Officer
                </p>
                <p className="text-xs font-mono font-bold text-[#0F2B48] leading-tight mt-0.5">
                  {username}
                </p>
              </div>
              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 text-slate-400 hover:text-red-700 hover:bg-red-50 rounded-lg border border-transparent hover:border-red-200 transition cursor-pointer"
                aria-label="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="flex-1 p-5 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </div>
      </main>
    </div>
  );
}