import Image from "next/image";
import logoImg from "../../public/logo.png";
import { ShieldCheck } from "lucide-react";

/** Sticky frosted-glass mobile navigation bar highlighting zero-PII privacy protection. */
export function TopPrivacyHeader() {
  return (
    <header className="sticky top-0 z-30 backdrop-blur-xl bg-white/80 border-b border-slate-200/80 px-4 py-3">
      <div className="max-w-md mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="relative h-11 w-11 shrink-0 rounded-2xl bg-gradient-to-br from-emerald-500/15 to-teal-600/20 border border-emerald-500/25 flex items-center justify-center p-1 shadow-sm">
            <Image
              src={logoImg}
              alt="MedSaathi Logo"
              className="h-full w-full object-contain"
              priority
            />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-900 leading-none">
              MedSaathi
            </h1>
            <p className="text-[11px] font-medium text-slate-500 mt-1">
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
