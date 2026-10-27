import { Activity, HelpCircle } from "lucide-react";

interface Props {
  labAbnormalities: string[];
  doctorQuestions: string[];
}

/** Displays out-of-range blood test values and 3 practical questions to ask the doctor. */
export function LabAndDoctorQuestionsCard({
  labAbnormalities,
  doctorQuestions,
}: Props) {
  if (!labAbnormalities.length && !doctorQuestions.length) return null;

  return (
    <section className="rounded-3xl bg-white border border-slate-200/80 p-5 shadow-sm space-y-5">
      {labAbnormalities.length > 0 && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-rose-600 flex items-center gap-1.5 mb-2.5">
            <Activity className="h-4 w-4" />
            Key Lab Findings (Out of Normal Range)
          </h3>
          <ul className="space-y-2">
            {labAbnormalities.map((item, i) => (
              <li
                key={i}
                className="text-xs text-slate-800 bg-rose-50/70 border border-rose-200/60 rounded-xl px-3.5 py-2.5 leading-relaxed"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {doctorQuestions.length > 0 && (
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-teal-700 flex items-center gap-1.5 mb-2.5">
            <HelpCircle className="h-4 w-4" />
            3 Questions to Ask Your Doctor
          </h3>
          <ul className="space-y-2">
            {doctorQuestions.map((q, i) => (
              <li
                key={i}
                className="text-xs text-slate-700 bg-slate-50 border border-slate-200/70 rounded-xl px-3.5 py-2.5 flex items-start gap-2"
              >
                <span className="font-bold text-teal-700">{i + 1}.</span>
                <span>{q}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
