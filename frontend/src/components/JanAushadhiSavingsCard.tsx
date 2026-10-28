import { IndianRupee, TrendingDown, CheckCircle, Sparkles } from "lucide-react";
import { GenericMatchResult } from "@/types/prescription_report_types";

interface Props {
  savingsList: GenericMatchResult[];
  totalMonthlySavingsInr: number;
}

/** Parses compound match source string into a clean badge and commercial reference. */
function parseMatchSource(source: string) {
  if (!source) {
    return { badge: "PMBJP Verified", commercialInfo: "" };
  }
  if (source.includes(" vs ")) {
    const [badgePart, mfgPart] = source.split(" vs ");
    return {
      badge: badgePart.trim(),
      commercialInfo: mfgPart.trim(),
    };
  }
  return { badge: source.trim(), commercialInfo: "" };
}

/** Compares prescribed branded MRPs against official Jan Aushadhi generic salt prices. */
export function JanAushadhiSavingsCard({
  savingsList,
  totalMonthlySavingsInr,
}: Props) {
  if (!savingsList.length) return null;

  return (
    <section className="rounded-3xl bg-gradient-to-br from-emerald-950 via-teal-900 to-slate-900 text-white p-5 shadow-lg border border-emerald-800/40 overflow-hidden">
      {/* Header Banner */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300 flex items-center gap-1.5">
            <TrendingDown className="h-3.5 w-3.5 text-emerald-400" />
            Jan Aushadhi Generic Bill Cutter
          </span>
          <h2 className="text-2xl font-black mt-1 text-white tracking-tight">
            Save ₹{totalMonthlySavingsInr.toLocaleString("en-IN")}
            <span className="text-xs font-semibold text-emerald-300 ml-1.5 font-normal">/ month</span>
          </h2>
        </div>
        <div className="h-12 w-12 rounded-2xl bg-emerald-500/20 border border-emerald-400/40 flex items-center justify-center shrink-0 shadow-inner">
          <IndianRupee className="h-6 w-6 text-emerald-300" />
        </div>
      </div>

      {/* Medication Comparison List */}
      <div className="space-y-3">
        {savingsList.map((item, idx) => {
          const { badge, commercialInfo } = parseMatchSource(item.match_source);
          const percentOff =
            item.branded_strip_price_inr > item.jan_aushadhi_strip_price_inr
              ? Math.round(
                  ((item.branded_strip_price_inr - item.jan_aushadhi_strip_price_inr) /
                    item.branded_strip_price_inr) *
                    100
                )
              : 0;

          return (
            <div
              key={idx}
              className="rounded-2xl bg-white/[0.08] backdrop-blur-md border border-white/10 p-3.5 transition-all hover:bg-white/[0.11]"
            >
              {/* Card Header: Brand Name + PMBJP Badge */}
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <h3 className="text-sm font-bold text-white truncate flex items-center gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-emerald-400 shrink-0" />
                    <span className="truncate">{item.prescribed_brand}</span>
                  </h3>
                </div>

                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/20 border border-emerald-400/30 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-200 shrink-0 max-w-[55%] truncate">
                  <CheckCircle className="h-3 w-3 text-emerald-300 shrink-0" />
                  <span className="truncate">{badge}</span>
                </span>
              </div>

              {/* Middle Box: Generic Salt Formulation & Manufacturer Info */}
              <div className="mt-2.5 rounded-xl bg-black/25 border border-white/5 p-2.5 space-y-1">
                <div className="flex items-center justify-between text-[10px]">
                  <span className="font-semibold text-emerald-300 uppercase tracking-wider">
                    Same Generic Formulation
                  </span>
                  {percentOff > 0 && (
                    <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-300 bg-emerald-500/20 px-1.5 py-0.2 rounded-md">
                      <Sparkles className="h-2.5 w-2.5" /> {percentOff}% Cheaper
                    </span>
                  )}
                </div>
                <p className="text-xs font-medium text-emerald-100 leading-snug">
                  {item.generic_salt_name}
                </p>
                {commercialInfo && (
                  <p className="text-[10px] text-slate-300/90 pt-1 border-t border-white/5 truncate">
                    <span className="text-slate-400 font-medium">Ref Brand:</span> {commercialInfo}
                  </p>
                )}
              </div>

              {/* Price Breakdown Grid */}
              <div className="mt-2.5 pt-2 border-t border-white/10 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-xl bg-white/[0.04] border border-white/5 p-1.5">
                  <span className="text-[10px] text-slate-300 block">Branded Strip</span>
                  <span className="text-xs font-semibold line-through text-rose-300">
                    ₹{item.branded_strip_price_inr}
                  </span>
                </div>
                <div className="rounded-xl bg-emerald-500/15 border border-emerald-400/25 p-1.5">
                  <span className="text-[10px] text-emerald-200 block font-medium">Jan Aushadhi</span>
                  <span className="text-xs font-bold text-emerald-300">
                    ₹{item.jan_aushadhi_strip_price_inr}
                  </span>
                </div>
                <div className="rounded-xl bg-emerald-400/20 border border-emerald-300/30 p-1.5">
                  <span className="text-[10px] text-emerald-200 block font-medium">Monthly Saved</span>
                  <span className="text-xs font-black text-white">
                    ₹{item.monthly_savings_inr}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

