"use client";

import { useRef, useState } from "react";
import { Volume2, Pause, Play, Share2 } from "lucide-react";
import { SimplifiedPrescriptionReport } from "@/types/prescription_report_types";
import { shareReportViaWhatsApp } from "@/services/whatsapp_family_sharer";

interface Props {
  report: SimplifiedPrescriptionReport;
  audioDataUrl: string;
}

/** High-contrast summary card with 1-tap native language audio playback and WhatsApp family sharing. */
export function GrandparentVoicePlayerCard({ report, audioDataUrl }: Props) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const toggleAudio = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play();
      setIsPlaying(true);
    }
  };

  return (
    <section className="rounded-3xl bg-white border border-slate-200/80 p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-teal-700">
          <Volume2 className="h-4 w-4" />
          Plain-Language Family Summary
        </span>
      </div>

      <p className="text-base font-medium text-slate-900 leading-relaxed mb-4">
        {report.patient_summary_translated}
      </p>

      <audio
        ref={audioRef}
        src={audioDataUrl}
        onEnded={() => setIsPlaying(false)}
        className="hidden"
      />

      <div className="flex gap-2.5">
        <button
          type="button"
          onClick={toggleAudio}
          className="flex-1 py-3.5 px-4 rounded-2xl bg-teal-50 hover:bg-teal-100/80 border border-teal-200 text-teal-900 font-semibold text-xs flex items-center justify-center gap-2 transition-all"
        >
          {isPlaying ? (
            <>
              <Pause className="h-4 w-4 fill-teal-900" />
              <span>Pause Voice Note</span>
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-teal-900" />
              <span>Listen in Selected Language</span>
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
