from datetime import datetime, timedelta
from typing import List
from schemas.prescription_response_schema import ExtractedMedicine


DOSE_SLOTS = [
    ("morning_dose", "Morning Medicine Dose", "080000"),
    ("afternoon_dose", "Afternoon Medicine Dose", "140000"),
    ("night_dose", "Night Medicine Dose", "210000"),
]


def build_medication_ics_content(medicines: List[ExtractedMedicine]) -> str:
    """Generates an RFC 5545 .ics calendar file string for 1-tap phone alarms."""
    today_str = datetime.now().strftime("%Y%m%d")
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//MedSaathi//Prescription Alarms//EN",
    ]

    for slot_attr, slot_title, time_hhmmss in DOSE_SLOTS:
        slot_meds = [m for m in medicines if getattr(m, slot_attr)]
        if not slot_meds:
            continue

        max_days = max((m.duration_days for m in slot_meds), default=5)
        med_descriptions = "\\n".join(
            f"- {m.brand_name} ({m.meal_instruction})" for m in slot_meds
        )

        ics_lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:{slot_title} ({len(slot_meds)} tablets)",
            f"DTSTART:{today_str}T{time_hhmmss}",
            f"DTEND:{today_str}T{time_hhmmss}",
            f"RRULE:FREQ=DAILY;COUNT={max_days}",
            f"DESCRIPTION:{med_descriptions}",
            "BEGIN:VALARM",
            "TRIGGER:-PT0M",
            "ACTION:DISPLAY",
            "DESCRIPTION:Time to take your medicine",
            "END:VALARM",
            "END:VEVENT",
        ])

    ics_lines.append("END:VCALENDAR")
    return "\r\n".join(ics_lines)
