import {
  Sun,
  CloudSun,
  Moon,
  AlertTriangle,
  BellPlus,
  Pill,
} from "lucide-react";
import { ExtractedMedicine } from "@/types/prescription_report_types";
import { downloadMedicationCalendarAlarms } from "@/services/calendar_alarm_downloader";

interface Props {
  medicines: ExtractedMedicine[];
  icsCalendarText: string;
}

/** Visual fridge-chart timetable displaying Morning/Afternoon/Night slots, food warnings, and 1-tap phone alarms. */
export function VisualPillScheduleCard({ medicines, icsCalendarText }: Props) {
  if (!medicines.length) return null;

  return (
    <section className="rounded-3xl bg-white border border-slate-200/80 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
            <Pill className="h-4 w-4 text-teal-600" />
            Daily Medicine Timetable
          </h2>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Visual schedule for parents & elders
          </p>
        </div>

        <button
          type="button"
          onClick={() => downloadMedicationCalendarAlarms(icsCalendarText)}
          className="py-2 px-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-[11px] font-semibold flex items-center gap-1.5 shadow-sm"
        >
          <BellPlus className="h-3.5 w-3.5 text-teal-400" />
          <span>Set Phone Alarms</span>
        </button>
      </div>

      <div className="space-y-3">
        {medicines.map((med, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-slate-200/90 bg-slate-50/60 p-3.5"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div>
                <h3 className="text-sm font-bold text-slate-900">
                  {med.brand_name}
                </h3>
                <p className="text-[11px] font-medium text-slate-500">
                  {med.active_chemical_salt} • {med.dosage_strength}
                </p>
              </div>
              <span className="shrink-0 rounded-lg bg-teal-100/80 text-teal-900 px-2.5 py-1 text-[11px] font-bold">
                {med.meal_instruction}
              </span>
            </div>

            <p className="text-xs text-slate-700 mb-3">{med.simple_purpose}</p>

            {/* 3-Column Morning / Afternoon / Night Visual Fridge Grid */}
            <div className="grid grid-cols-3 gap-2 text-center">
              <div
                className={`py-2 px-2 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 ${
                  med.morning_dose
                    ? "bg-amber-50 border-amber-300 text-amber-950"
                    : "bg-white/50 border-slate-200/60 text-slate-300"
                }`}
              >
                <Sun className="h-4 w-4" />
                <span>{med.morning_dose ? "1 Tablet" : "—"}</span>
                <span className="text-[10px] font-normal">Morning</span>
              </div>

              <div
                className={`py-2 px-2 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 ${
                  med.afternoon_dose
                    ? "bg-sky-50 border-sky-300 text-sky-950"
                    : "bg-white/50 border-slate-200/60 text-slate-300"
                }`}
              >
                <CloudSun className="h-4 w-4" />
                <span>{med.afternoon_dose ? "1 Tablet" : "—"}</span>
                <span className="text-[10px] font-normal">Afternoon</span>
              </div>

              <div
                className={`py-2 px-2 rounded-xl border text-xs font-semibold flex flex-col items-center gap-1 ${
                  med.night_dose
                    ? "bg-indigo-50 border-indigo-300 text-indigo-950"
                    : "bg-white/50 border-slate-200/60 text-slate-300"
                }`}
              >
                <Moon className="h-4 w-4" />
                <span>{med.night_dose ? "1 Tablet" : "—"}</span>
                <span className="text-[10px] font-normal">Night</span>
              </div>
            </div>

            {med.food_or_drug_clash_warning && (
              <div className="mt-3 rounded-xl bg-amber-50/90 border border-amber-200/90 px-3 py-2 flex items-start gap-2 text-[11px] font-medium text-amber-950">
                <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <span>{med.food_or_drug_clash_warning}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
