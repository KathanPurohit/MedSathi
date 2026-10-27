import { IndianRupee, TrendingDown, CheckCircle } from "lucide-react";
import { GenericMatchResult } from "@/types/prescription_report_types";

interface Props {
  savingsList: GenericMatchResult[];
  totalMonthlySavingsInr: number;
}

/** Compares prescribed branded MRPs against official Jan Aushadhi generic salt prices. */
export function JanAushadhiSavingsCard({
  savingsList,
  totalMonthlySavingsInr,
}: Props) {
  if (!savingsList.length) return null;

  return (
    <section className="rounded-3xl bg-gradient-to-br from-emerald-900 via-teal-900 to-slate-900 text-white p-5 shadow-md">
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-300 flex items-center gap-1">
            <TrendingDown className="h-3.5 w-3.5" />
            Jan Aushadhi Generic Bill Cutter
          </span>
          <h2 className="text-xl font-extrabold mt-1">
            Save ₹{totalMonthlySavingsInr.toLocaleString("en-IN")} / month
          </h2>
        </div>
        <div className="h-11 w-11 rounded-2xl bg-emerald-500/20 border border-emerald-400/30 flex items-center justify-center">
          <IndianRupee className="h-5 w-5 text-emerald-300" />
        </div>
      </div>

      <div className="space-y-2.5">
        {savingsList.map((item, idx) => (
          <div
            key={idx}
            className="rounded-2xl bg-white/10 backdrop-blur-sm border border-white/10 p-3.5"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-xs font-bold text-white">
                  {item.prescribed_brand}
                </p>
                <p className="text-[11px] text-emerald-200 mt-0.5">
                  Same Salt: {item.generic_salt_name}
                </p>
              </div>
              <span className="rounded-lg bg-emerald-400/20 border border-emerald-300/30 px-2 py-0.5 text-[10px] font-semibold text-emerald-200 flex items-center gap-1 shrink-0">
                <CheckCircle className="h-3 w-3" /> {item.match_source}
              </span>
            </div>

            <div className="mt-3 pt-2.5 border-t border-white/10 grid grid-cols-3 gap-2 text-xs">
              <div>
                <span className="text-[10px] text-slate-300 block">
                  Branded Strip
                </span>
                <span className="font-semibold line-through text-rose-300">
                  ₹{item.branded_strip_price_inr}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-300 block">
                  Jan Aushadhi
                </span>
                <span className="font-bold text-emerald-300">
                  ₹{item.jan_aushadhi_strip_price_inr}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-slate-300 block">
                  Monthly Saved
                </span>
                <span className="font-bold text-white">
                  ₹{item.monthly_savings_inr}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
