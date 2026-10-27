/** Triggers a 1-tap browser download of the .ics alarm file to open native phone calendars. */
export function downloadMedicationCalendarAlarms(icsText: string): void {
  const blob = new Blob([icsText], { type: "text/calendar;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "medsaathi-pill-reminders.ics";
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}
