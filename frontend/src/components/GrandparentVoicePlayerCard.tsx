"use client";

import { useEffect, useRef, useState } from "react";
import { Volume2, Pause, Play, Share2, Loader2, Mic } from "lucide-react";
import {
  SimplifiedPrescriptionReport,
  SupportedLanguage,
  VoiceGender,
} from "@/types/prescription_report_types";
import { shareReportViaWhatsApp } from "@/services/whatsapp_family_sharer";
import { generateVoiceNote } from "@/services/analyze_document_client";

interface Props {
  report: SimplifiedPrescriptionReport;
  audioDataUrl: string;
  language: SupportedLanguage;
  initialVoiceGender?: VoiceGender;
}

const VOICE_LABELS: Record<
  SupportedLanguage,
  { female: string; male: string }
> = {
  English: {
    female: "Dr. Neerja (Warm Caregiver)",
    male: "Dr. Prabhat (Calm Doctor)",
  },
  Hindi: {
    female: "डॉ. स्वरा (महिला स्वर)",
    male: "डॉ. मधुर (पुरुष स्वर)",
  },
  Gujarati: {
    female: "ડૉ. ધ્વનિ (મહિલા અવાજ)",
    male: "ડૉ. નિરંજન (પુરુષ અવાજ)",
  },
};

/** High-contrast summary card with 1-tap native language audio playback, instant voice persona switching, and WhatsApp family sharing. */
export function GrandparentVoicePlayerCard({
  report,
  audioDataUrl,
  language,
  initialVoiceGender = "female",
}: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeGender, setActiveGender] = useState<VoiceGender>(initialVoiceGender);
  const [isSwitchingVoice, setIsSwitchingVoice] = useState(false);

  // Cache generated audio per gender so switching is instant
  const [audioCache, setAudioCache] = useState<Record<VoiceGender, string>>({
    female: initialVoiceGender === "female" ? audioDataUrl : "",
    male: initialVoiceGender === "male" ? audioDataUrl : "",
  });

  useEffect(() => {
    setAudioCache((prev) => ({
      female: activeGender === "female" ? audioDataUrl : prev.female,
      male: activeGender === "male" ? audioDataUrl : prev.male,
    }));
  }, [audioDataUrl, activeGender]);

  const currentAudioSrc = audioCache[activeGender] || audioDataUrl;

  const toggleAudio = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().then(() => setIsPlaying(true)).catch(() => setIsPlaying(false));
    }
  };

  const handleSwitchVoice = async (gender: VoiceGender) => {
    if (gender === activeGender || isSwitchingVoice) return;

    const wasPlaying = isPlaying;
    if (audioRef.current && wasPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    }

    if (audioCache[gender]) {
      setActiveGender(gender);
      if (wasPlaying && audioRef.current) {
        setTimeout(() => {
          audioRef.current?.play().then(() => setIsPlaying(true)).catch(() => {});
        }, 150);
      }
      return;
    }

    // Generate new voice on-demand
    setIsSwitchingVoice(true);
    try {
      const newAudioUrl = await generateVoiceNote(
        report.voice_script_translated,
        language,
        gender
      );
      setAudioCache((prev) => ({
        female: gender === "female" ? newAudioUrl : prev.female,
        male: gender === "male" ? newAudioUrl : prev.male,
      }));
      setActiveGender(gender);
      if (wasPlaying && audioRef.current) {
        setTimeout(() => {
          audioRef.current?.play().then(() => setIsPlaying(true)).catch(() => {});
        }, 150);
      }
    } catch (err) {
      console.error("Failed to switch doctor voice:", err);
    } finally {
      setIsSwitchingVoice(false);
    }
  };

  const labels = VOICE_LABELS[language] || VOICE_LABELS.English;

  return (
    <section className="rounded-3xl bg-white border border-slate-200/80 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-teal-700">
          <Volume2 className="h-4 w-4" />
          Plain-Language Family Summary
        </span>

        {/* Voice persona pills */}
        <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-xl text-[10px] font-semibold">
          <button
            type="button"
            disabled={isSwitchingVoice}
            onClick={() => handleSwitchVoice("female")}
            className={`px-2 py-1 rounded-lg transition-all flex items-center gap-1 ${
              activeGender === "female"
                ? "bg-white text-teal-900 shadow-sm"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            <span>Female</span>
          </button>
          <button
            type="button"
            disabled={isSwitchingVoice}
            onClick={() => handleSwitchVoice("male")}
            className={`px-2 py-1 rounded-lg transition-all flex items-center gap-1 ${
              activeGender === "male"
                ? "bg-white text-teal-900 shadow-sm"
                : "text-slate-500 hover:text-slate-800"
            }`}
          >
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
            <span>Male</span>
          </button>
        </div>
      </div>

      <p className="text-base font-medium text-slate-900 leading-relaxed mb-3">
        {report.patient_summary_translated}
      </p>

      {/* Active voice banner */}
      <div className="mb-4 flex items-center justify-between px-3 py-2 rounded-xl bg-slate-50 border border-slate-200/70 text-[11px] text-slate-600">
        <span className="flex items-center gap-1.5">
          <Mic className="h-3.5 w-3.5 text-teal-600" />
          Narrated by: <strong>{activeGender === "female" ? labels.female : labels.male}</strong>
        </span>
        {isSwitchingVoice && (
          <span className="flex items-center gap-1 text-teal-700 font-semibold animate-pulse">
            <Loader2 className="h-3 w-3 animate-spin" /> Generating voice...
          </span>
        )}
      </div>

      <audio
        ref={audioRef}
        src={currentAudioSrc}
        onEnded={() => setIsPlaying(false)}
        className="hidden"
      />

      <div className="flex gap-2.5">
        <button
          type="button"
          disabled={isSwitchingVoice}
          onClick={toggleAudio}
          className="flex-1 py-3.5 px-4 rounded-2xl bg-teal-50 hover:bg-teal-100/80 border border-teal-200 text-teal-900 font-semibold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-60"
        >
          {isPlaying ? (
            <>
              <Pause className="h-4 w-4 fill-teal-900" />
              <span>Pause Voice Note</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-teal-900" />
              <span>Listen in {language}</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={() => shareReportViaWhatsApp(report)}
          className="py-3.5 px-4 rounded-2xl bg-[#25D366]/10 hover:bg-[#25D366]/20 border border-[#25D366]/30 text-emerald-950 font-semibold text-xs flex items-center justify-center gap-1.5 transition-all"
        >
          <Share2 className="h-4 w-4 text-emerald-700" />
          <span>WhatsApp</span>
        </button>
      </div>
    </section>
  );
}
