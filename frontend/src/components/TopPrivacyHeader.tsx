import { ShieldCheck, Sparkles } from "lucide-react";

/** Sticky frosted-glass mobile navigation bar highlighting zero-PII privacy protection. */
export function TopPrivacyHeader() {
  return (
    <header className="sticky top-0 z-30 backdrop-blur-xl bg-white/80 border-b border-slate-200/80 px-4 py-3.5">
      <div className="max-w-md mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-teal-600 to-emerald-500 flex items-center justify-center text-white shadow-sm shadow-teal-600/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-900 leading-none">
              MedSaathi
            </h1>
            <p className="text-[11px] font-medium text-slate-500 mt-0.5">
              Rx & Lab Simplifier • Jan Aushadhi Finder
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200/70 px-2.5 py-1 text-[11px] font-semibold text-emerald-800">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
          <span>Auto-PII Redacted</span>
        </div>
      </div>
    </header>
  );
}
