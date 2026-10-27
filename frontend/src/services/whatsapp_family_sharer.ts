import { SimplifiedPrescriptionReport } from "@/types/prescription_report_types";

/** Formats a clean family summary message and opens native WhatsApp sharing. */
export function shareReportViaWhatsApp(
  report: SimplifiedPrescriptionReport
): void {
  const medLines = report.medicines
    .map((m) => {
      const slots = [
        m.morning_dose ? "☀️ Morning" : "",
        m.afternoon_dose ? "🌤️ Afternoon" : "",
        m.night_dose ? "🌙 Night" : "",
      ]
        .filter(Boolean)
        .join(", ");
      return `• *${m.brand_name}* (${slots} - ${m.meal_instruction})`;
    })
    .join("\n");

  const text = [
    "🩺 *MedSaathi Family Prescription Summary*",
    "",
    report.patient_summary_translated,
    "",
    "💊 *Daily Medicine Timetable:*",
    medLines || "See attached report",
    "",
    `💰 *Potential Jan Aushadhi Savings:* ₹${report.total_monthly_savings_inr}/month`,
  ].join("\n");

  window.open(
    `https://wa.me/?text=${encodeURIComponent(text)}`,
    "_blank",
    "noopener,noreferrer"
  );
}
