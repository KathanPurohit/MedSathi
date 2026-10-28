"use client";

import { useRef } from "react";
import Image from "next/image";
import logoImg from "../../public/logo.png";
import { Camera, FileUp, Globe, Lock, Mic } from "lucide-react";
import { SupportedLanguage, VoiceGender } from "@/types/prescription_report_types";

interface Props {
  selectedLanguage: SupportedLanguage;
  onSelectLanguage: (lang: SupportedLanguage) => void;
  selectedVoiceGender: VoiceGender;
  onSelectVoiceGender: (gender: VoiceGender) => void;
  onFileSelected: (file: File) => void;
  isAnalyzing: boolean;
}

const LANGUAGES: { id: SupportedLanguage; label: string; native: string }[] = [
  { id: "English", label: "English", native: "EN" },
  { id: "Hindi", label: "हिंदी", native: "HI" },
  { id: "Gujarati", label: "ગુજરાતી", native: "GU" },
];

const VOICE_PERSONAS: Record<
  SupportedLanguage,
  { female: string; male: string }
> = {
  English: { female: "Dr. Neerja (Female Caregiver)", male: "Dr. Prabhat (Male Doctor)" },
  Hindi: { female: "डॉ. स्वरा (महिला स्वर)", male: "डॉ. मधुर (पुरुष स्वर)" },
  Gujarati: { female: "ડૉ. ધ્વનિ (મહિલા અવાજ)", male: "ડૉ. નિરંજન (પુરુષ અવાજ)" },
};

/** Hero card allowing language & doctor voice selection and 1-tap camera or gallery prescription upload. */
export function LanguageAndUploadCard({
  selectedLanguage,
  onSelectLanguage,
  selectedVoiceGender,
  onSelectVoiceGender,
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

  const currentPersonas = VOICE_PERSONAS[selectedLanguage];

  return (
    <section className="rounded-3xl bg-white border border-slate-200/80 p-5 shadow-sm">
      {/* Brand Hero Welcome Banner */}
      <div className="flex items-center gap-3 pb-3.5 mb-3.5 border-b border-slate-100">
        <div className="relative h-12 w-12 shrink-0 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-teal-600/15 border border-emerald-500/20 flex items-center justify-center p-1.5 shadow-sm">
          <Image
            src={logoImg}
            alt="MedSaathi Logo"
            className="h-full w-full object-contain"
            priority
          />
        </div>
        <div>
          <h2 className="text-sm font-bold text-slate-900 leading-tight">
            MedSaathi AI Prescription Assistant
          </h2>
          <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
            Zero-PII local scrub • Jan Aushadhi generic savings
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Globe className="h-3.5 w-3.5 text-teal-600" />
          1. Select Output Language
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 p-1 rounded-2xl bg-slate-100/80 mb-4">
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

      {/* Voice Persona Selector */}
      <div className="mb-5">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Mic className="h-3.5 w-3.5 text-teal-600" />
            2. Choose Doctor Voice
          </span>
        </div>
        <div className="grid grid-cols-2 gap-2 p-1 rounded-2xl bg-slate-100/80">
          <button
            type="button"
            onClick={() => onSelectVoiceGender("female")}
            className={`py-2 px-3 rounded-xl text-[11px] font-semibold transition-all flex items-center justify-center gap-1.5 ${
              selectedVoiceGender === "female"
                ? "bg-white text-teal-900 shadow-sm ring-1 ring-slate-200/70"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-teal-500 shrink-0" />
            <span className="truncate">{currentPersonas.female}</span>
          </button>
          <button
            type="button"
            onClick={() => onSelectVoiceGender("male")}
            className={`py-2 px-3 rounded-xl text-[11px] font-semibold transition-all flex items-center justify-center gap-1.5 ${
              selectedVoiceGender === "male"
                ? "bg-white text-teal-900 shadow-sm ring-1 ring-slate-200/70"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-blue-500 shrink-0" />
            <span className="truncate">{currentPersonas.male}</span>
          </button>
        </div>
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
        accept="image/*,application/pdf,.pdf"
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
          className="w-full py-3.5 px-4 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200/80 text-slate-700 font-medium text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-60"
        >
          <FileUp className="h-4 w-4 text-teal-600" />
          <span>Upload Multi-Page PDF or Gallery Photo</span>
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
