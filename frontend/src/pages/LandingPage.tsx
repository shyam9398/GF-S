import { Link } from "react-router-dom";
import {
  FileText,
  Cpu,
  BookmarkCheck,
  CheckCircle2,
  ArrowRight,
  Shield,
  Layers,
  Search,
  ExternalLink,
  ChevronRight,
  FileCheck,
  SlidersHorizontal,
  Lock,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 font-sans flex flex-col selection:bg-blue-100 selection:text-blue-900">
      {/* Top Official National Banner */}
      <div className="border-b border-slate-200 bg-white text-slate-700 text-[11px] sm:text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-1.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-600" />
            <span className="font-semibold text-slate-800">भारत सरकार | Government of India</span>
            <span className="text-slate-300 hidden md:inline">•</span>
            <span className="hidden md:inline text-slate-600">उपभोक्ता मामले, खाद्य और सार्वजनिक वितरण मंत्रालय</span>
          </div>
          <div className="flex items-center gap-4 text-slate-500">
            <span className="font-medium text-slate-700">मानक पथप्रदर्शक | BIS</span>
            <a
              href="https://www.services.bis.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-blue-700 inline-flex items-center gap-1 transition"
            >
              BIS Care <ExternalLink size={10} />
            </a>
          </div>
        </div>
      </div>

      {/* Main Official Header */}
      <header className="sticky top-0 z-40 bg-white border-b border-slate-200 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          {/* Logo & Platform Name */}
          <Link to="/" className="flex items-center gap-3.5 group">
            <div className="h-11 w-11 rounded-lg bg-[#0F2B48] text-white flex items-center justify-center font-black tracking-wider text-sm shadow-xs border border-blue-950">
              <span className="text-[#DC2626] mr-0.5">I</span>IS
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base sm:text-lg font-bold text-[#0F2B48] tracking-tight leading-tight">
                  IISCAE
                </span>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-red-50 text-[#DC2626] border border-red-200 rounded">
                  BIS Engine
                </span>
              </div>
              <p className="text-xs font-semibold text-slate-600 hidden sm:block">
                Intelligent Indian Standards Context-Aware Engine
              </p>
              <p className="text-[11px] text-slate-500 hidden md:block">
                Bureau of Indian Standards • Procurement Intelligence
              </p>
            </div>
          </Link>

          {/* Action CTAs */}
          <div className="flex items-center gap-2.5 sm:gap-3">
            <Link
              to="/login"
              className="px-3.5 py-2 text-xs sm:text-sm font-semibold text-[#0F2B48] hover:text-blue-900 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg transition shadow-2xs"
            >
              Sign In
            </Link>
            <Link
              to="/procurement-officer"
              className="px-4 py-2 text-xs sm:text-sm font-semibold text-white bg-[#0F2B48] hover:bg-[#163c63] border border-[#0A1F33] rounded-lg transition shadow-xs flex items-center gap-1.5"
            >
              <Shield size={14} className="text-red-400" />
              <span>Procurement Officer</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="border-b border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-20">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-12 items-center">
            {/* Hero Left Content */}
            <div className="lg:col-span-7 space-y-6">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-md bg-blue-50 border border-blue-200 text-blue-900 text-xs font-bold tracking-wide">
                <span className="w-2 h-2 rounded-full bg-[#DC2626]" />
                BIS PROCUREMENT INTELLIGENCE
              </div>

              {/* Headings */}
              <div className="space-y-3">
                <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-[#0F2B48] tracking-tight leading-[1.15]">
                  Find the Right Indian Standards for Every Procurement
                </h1>
                <p className="text-base sm:text-lg font-semibold text-blue-950/80">
                  Intelligent BIS Standards Discovery for Procurement Specifications
                </p>
                <p className="text-sm sm:text-base text-slate-600 leading-relaxed max-w-2xl">
                  AI-powered analysis that transforms procurement specifications into applicable BIS standards with traceable evidence and recommendation rationale.
                </p>
              </div>

              {/* Bullet Highlights */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
                {[
                  "Upload procurement specifications",
                  "Extract technical requirements",
                  "Discover relevant Indian Standards",
                  "Validate applicability",
                  "Get evidence-backed recommendations",
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs sm:text-sm font-medium text-slate-700">
                    <CheckCircle2 size={16} className="text-emerald-600 shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-4">
                <Link
                  to="/procurement-officer"
                  className="px-6 py-3 text-sm font-bold text-white bg-[#0F2B48] hover:bg-[#163c63] border border-[#0A1F33] rounded-lg transition shadow-sm inline-flex items-center gap-2"
                >
                  <Shield size={16} className="text-red-400" />
                  <span>Procurement Officer</span>
                  <ChevronRight size={16} />
                </Link>

                <Link
                  to="/login"
                  className="px-6 py-3 text-sm font-bold text-slate-800 bg-white hover:bg-slate-50 border border-slate-300 rounded-lg transition shadow-2xs inline-flex items-center gap-2"
                >
                  <span>Sign In</span>
                  <ArrowRight size={15} />
                </Link>
              </div>

              {/* Officer Note */}
              <p className="text-xs text-slate-500 pt-1 flex items-center gap-1.5">
                <Lock size={12} className="text-slate-400" />
                <span>Authorized official access requires designated officer credentials ending with <code className="px-1.5 py-0.5 bg-slate-100 rounded text-slate-800 font-mono text-[11px]">.bis</code></span>
              </p>
            </div>

            {/* Hero Right Visual Diagram */}
            <div className="lg:col-span-5">
              <div className="bg-[#F8FAFC] border border-slate-200 rounded-xl p-5 sm:p-6 shadow-xs">
                {/* Visual Header */}
                <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-200">
                  <div>
                    <h3 className="text-xs font-bold text-[#0F2B48] uppercase tracking-wider">
                      Standards Discovery Pipeline
                    </h3>
                    <p className="text-[11px] text-slate-500">Autonomous 4-Stage Verification Workflow</p>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Active System
                  </span>
                </div>

                {/* Vertical Process Steps representing:
                    Procurement Document → AI Analysis → BIS Standards → Recommendation */}
                <div className="space-y-3 relative">
                  {/* Step 1: Procurement Document */}
                  <div className="bg-white rounded-lg p-3.5 border border-slate-200 shadow-2xs relative">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-blue-50 text-blue-700 border border-blue-100 shrink-0">
                        <FileText size={18} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-[#0F2B48]">Procurement Document</p>
                          <span className="text-[10px] font-mono text-slate-400">STAGE 01</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Tender specification upload, BoQ clauses, and scope extraction
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Flow Arrow */}
                  <div className="flex justify-center -my-1">
                    <div className="w-0.5 h-3 bg-slate-300" />
                  </div>

                  {/* Step 2: AI Analysis */}
                  <div className="bg-white rounded-lg p-3.5 border border-slate-200 shadow-2xs relative">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-amber-50 text-amber-700 border border-amber-100 shrink-0">
                        <Cpu size={18} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-[#0F2B48]">AI Analysis</p>
                          <span className="text-[10px] font-mono text-slate-400">STAGE 02</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Docling clause segmentation & Gemini semantic parameter structuring
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Flow Arrow */}
                  <div className="flex justify-center -my-1">
                    <div className="w-0.5 h-3 bg-slate-300" />
                  </div>

                  {/* Step 3: BIS Standards */}
                  <div className="bg-white rounded-lg p-3.5 border border-slate-200 shadow-2xs relative">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-100 shrink-0">
                        <Search size={18} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-[#0F2B48]">BIS Standards</p>
                          <span className="text-[10px] font-mono text-slate-400">STAGE 03</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Indian Standards database retrieval & normative cross-reference mapping
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Flow Arrow */}
                  <div className="flex justify-center -my-1">
                    <div className="w-0.5 h-3 bg-slate-300" />
                  </div>

                  {/* Step 4: Recommendation */}
                  <div className="bg-white rounded-lg p-3.5 border-2 border-emerald-500/80 shadow-2xs relative bg-emerald-50/20">
                    <div className="flex items-start gap-3">
                      <div className="p-2 rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200 shrink-0">
                        <BookmarkCheck size={18} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-bold text-[#0F2B48]">Recommendation</p>
                          <span className="text-[10px] font-mono font-bold text-emerald-700">FINAL VERDICT</span>
                        </div>
                        <p className="text-[11px] text-slate-600 mt-0.5">
                          Applicability categorization with traceable clause evidence & justification
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer metadata */}
                <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="font-medium text-slate-600">Applicability Engine</span>
                  <span className="font-mono text-slate-400">GFR 2017 Rule 144(i)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Section */}
      <section className="py-14 sm:py-20 bg-[#F8FAFC] border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-12">
            <p className="text-xs font-bold uppercase tracking-wider text-[#DC2626]">
              Core Capabilities
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-[#0F2B48] mt-1.5 tracking-tight">
              Engineered for Public Procurement Officers
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 mt-2">
              Transforming procurement compliance evaluation from manual standard searches into deterministic, evidence-backed recommendations.
            </p>
          </div>

          {/* 4 Feature Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 01 */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs hover:shadow-xs transition">
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-black text-[#0F2B48]/30 font-mono">01</span>
                <div className="p-2 rounded-lg bg-blue-50 text-blue-700">
                  <FileCheck size={20} />
                </div>
              </div>
              <h3 className="text-base font-bold text-[#0F2B48] mb-2">
                Specification Analysis
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Extract product and technical requirements from procurement documents.
              </p>
            </div>

            {/* Feature 02 */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs hover:shadow-xs transition">
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-black text-[#0F2B48]/30 font-mono">02</span>
                <div className="p-2 rounded-lg bg-indigo-50 text-indigo-700">
                  <Search size={20} />
                </div>
              </div>
              <h3 className="text-base font-bold text-[#0F2B48] mb-2">
                BIS Standards Discovery
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Find relevant Indian Standards using semantic search.
              </p>
            </div>

            {/* Feature 03 */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs hover:shadow-xs transition">
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-black text-[#0F2B48]/30 font-mono">03</span>
                <div className="p-2 rounded-lg bg-amber-50 text-amber-700">
                  <SlidersHorizontal size={20} />
                </div>
              </div>
              <h3 className="text-base font-bold text-[#0F2B48] mb-2">
                Applicability Validation
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Identify primary, normative, allied, supporting and non-applicable standards.
              </p>
            </div>

            {/* Feature 04 */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-2xs hover:shadow-xs transition">
              <div className="flex items-center justify-between mb-4">
                <span className="text-2xl font-black text-[#0F2B48]/30 font-mono">04</span>
                <div className="p-2 rounded-lg bg-emerald-50 text-emerald-700">
                  <Layers size={20} />
                </div>
              </div>
              <h3 className="text-base font-bold text-[#0F2B48] mb-2">
                Evidence & Traceability
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Show why each standard was recommended with supporting evidence.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Standards Classification Matrix Breakdown */}
      <section className="py-14 sm:py-16 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-5 space-y-4">
              <span className="text-xs font-bold uppercase tracking-wider text-[#DC2626]">
                Comprehensive BIS Categorization
              </span>
              <h2 className="text-2xl sm:text-3xl font-bold text-[#0F2B48] tracking-tight">
                Traceable Rationale Across 6 Standard Tiers
              </h2>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Every extracted procurement clause is cross-validated against the Bureau of Indian Standards catalog to prevent non-compliance in tender awards.
              </p>
              <div className="pt-2">
                <Link
                  to="/procurement-officer"
                  className="inline-flex items-center gap-2 text-xs font-bold text-blue-700 hover:text-blue-900"
                >
                  <span>Launch Procurement Officer Workspace</span>
                  <ArrowRight size={14} />
                </Link>
              </div>
            </div>

            <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-3.5">
              {[
                { title: "Primary Applicable", desc: "Core Indian Standard dictating overall product conformance.", color: "border-blue-200 bg-blue-50/50 text-blue-900" },
                { title: "Normative References", desc: "Mandatory referenced standards embedded in the primary specification.", color: "border-indigo-200 bg-indigo-50/50 text-indigo-900" },
                { title: "Allied Standards", desc: "Directly related domain standards for associated assemblies.", color: "border-purple-200 bg-purple-50/50 text-purple-900" },
                { title: "Supporting Standards", desc: "Guidelines covering raw materials, sampling, and tolerances.", color: "border-amber-200 bg-amber-50/50 text-amber-900" },
                { title: "Verification & Testing", desc: "Prescribed laboratory testing methods and test protocols.", color: "border-emerald-200 bg-emerald-50/50 text-emerald-900" },
                { title: "Not Applicable", desc: "Standards evaluated and ruled out with explicit exclusion rationale.", color: "border-slate-200 bg-slate-50 text-slate-700" },
              ].map((tier, idx) => (
                <div key={idx} className={`p-3.5 rounded-lg border ${tier.color}`}>
                  <p className="text-xs font-bold">{tier.title}</p>
                  <p className="text-[11px] text-slate-600 mt-1">{tier.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Official Government Footer */}
      <footer className="mt-auto bg-[#0F2B48] text-white border-t border-slate-800 text-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 pb-8 border-b border-slate-700/60">
            {/* Col 1 */}
            <div className="md:col-span-2 space-y-3">
              <div className="flex items-center gap-2">
                <span className="font-bold text-sm tracking-wide">IISCAE</span>
                <span className="text-[11px] text-slate-300">| BIS Procurement Recommendation Engine</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed max-w-md">
                Developed for Smart India Hackathon (SIH 2026) Problem Statement 26108.
                Empowering public procurement departments with AI-driven BIS standards discovery, applicability classification, and traceable evidence.
              </p>
            </div>

            {/* Col 2 */}
            <div>
              <p className="font-bold text-slate-200 mb-3 uppercase tracking-wider text-[11px]">
                Official Portals
              </p>
              <ul className="space-y-2 text-slate-300 text-xs">
                <li>
                  <a href="https://www.bis.gov.in" target="_blank" rel="noreferrer" className="hover:text-white transition flex items-center gap-1">
                    Bureau of Indian Standards <ExternalLink size={10} />
                  </a>
                </li>
                <li>
                  <a href="https://www.services.bis.gov.in" target="_blank" rel="noreferrer" className="hover:text-white transition flex items-center gap-1">
                    BIS Care Portal <ExternalLink size={10} />
                  </a>
                </li>
                <li>
                  <a href="https://gem.gov.in" target="_blank" rel="noreferrer" className="hover:text-white transition flex items-center gap-1">
                    Government e-Marketplace (GeM) <ExternalLink size={10} />
                  </a>
                </li>
              </ul>
            </div>

            {/* Col 3 */}
            <div>
              <p className="font-bold text-slate-200 mb-3 uppercase tracking-wider text-[11px]">
                Procurement Access
              </p>
              <ul className="space-y-2 text-slate-300 text-xs">
                <li>
                  <Link to="/procurement-officer" className="hover:text-white transition">
                    Procurement Officer Access
                  </Link>
                </li>
                <li>
                  <Link to="/login" className="hover:text-white transition">
                    Officer Sign In
                  </Link>
                </li>
                <li>
                  <Link to="/signup" className="hover:text-white transition">
                    Create Officer Account
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between text-[11px] text-slate-400 gap-2">
            <p>© {new Date().getFullYear()} Bureau of Indian Standards & Department of Consumer Affairs. Government of India.</p>
            <p>GFR 2017 Rule 144(i) BIS Mandate Compliant</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
