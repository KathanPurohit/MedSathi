"use client";

import { useRef } from "react";
import { Camera, FileUp, Globe, Lock } from "lucide-react";
import { SupportedLanguage } from "@/types/prescription_report_types";

interface Props {
  selectedLanguage: SupportedLanguage;
  onSelectLanguage: (lang: SupportedLanguage) => void;
  onFileSelected: (file: File) => void;
  isAnalyzing: boolean;
}

const LANGUAGES: { id: SupportedLanguage; label: string; native: string }[] = [
  { id: "English", label: "English", native: "EN" },
  { id: "Hindi", label: "हिंदी", native: "HI" },
  { id: "Gujarati", label: "ગુજરાતી", native: "GU" },
];

/** Hero card allowing language selection and 1-tap camera or gallery prescription upload. */
export function LanguageAndUploadCard({
  selectedLanguage,
  onSelectLanguage,
  onFileSelected,
  isAnalyzing,
}: Props) {
  const cameraInputRef = useRef<HTMLInputElement>(null);
  const galleryInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelected(file);
    e.target.value = "";
  };

  return (
    <section className="rounded-3xl bg-white border border-slate-200/80 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Globe className="h-3.5 w-3.5 text-teal-600" />
          1. Select Output Language
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 p-1 rounded-2xl bg-slate-100/80 mb-5">
        {LANGUAGES.map((lang) => {
          const active = selectedLanguage === lang.id;
          return (
            <button
              key={lang.id}
              type="button"
              onClick={() => onSelectLanguage(lang.id)}
              className={`py-2.5 px-3 rounded-xl text-xs font-semibold transition-all ${
                active
                  ? "bg-white text-teal-900 shadow-sm ring-1 ring-slate-200/70"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {lang.label}
            </button>
          );
        })}
      </div>

      {/* Hidden inputs for Rear Camera vs Photo Gallery */}
      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileChange}
        className="hidden"
      />
      <input
        ref={galleryInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="space-y-2.5">
        <button
          type="button"
          disabled={isAnalyzing}
          onClick={() => cameraInputRef.current?.click()}
          className="w-full py-4 px-5 rounded-2xl bg-gradient-to-r from-teal-700 to-emerald-600 hover:from-teal-800 hover:to-emerald-700 active:scale-[0.99] text-white font-semibold text-sm shadow-md shadow-teal-700/20 flex items-center justify-center gap-2.5 transition-all disabled:opacity-60"
        >
          <Camera className="h-5 w-5" />
          <span>Snap Prescription or Lab Report</span>
        </button>

        <button
          type="button"
          disabled={isAnalyzing}
          onClick={() => galleryInputRef.current?.click()}
          className="w-full py-3 px-4 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200/80 text-slate-700 font-medium text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-60"
        >
          <FileUp className="h-4 w-4 text-slate-500" />
          <span>Or Upload Photo from Gallery</span>
        </button>
      </div>

      <div className="mt-4 pt-3.5 border-t border-slate-100 flex items-start gap-2 text-[11px] text-slate-500 leading-relaxed">
        <Lock className="h-3.5 w-3.5 text-emerald-600 shrink-0 mt-0.5" />
        <span>
          <strong>Dual Privacy Shield:</strong> Swipe over any name on the next
          screen, plus our offline OCR automatically blacks out phone numbers &
          patient IDs before AI analysis.
        </span>
      </div>
    </section>
  );
}
