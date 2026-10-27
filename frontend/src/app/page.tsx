"use client";

import { useState } from "react";
import { Loader2, ShieldAlert } from "lucide-react";
import { TopPrivacyHeader } from "@/components/TopPrivacyHeader";
import { LanguageAndUploadCard } from "@/components/LanguageAndUploadCard";
import { TouchPrivacyRedactorModal } from "@/components/TouchPrivacyRedactorModal";
import { RedactedProofPreview } from "@/components/RedactedProofPreview";
import { GrandparentVoicePlayerCard } from "@/components/GrandparentVoicePlayerCard";
import { VisualPillScheduleCard } from "@/components/VisualPillScheduleCard";
import { JanAushadhiSavingsCard } from "@/components/JanAushadhiSavingsCard";
import { LabAndDoctorQuestionsCard } from "@/components/LabAndDoctorQuestionsCard";
import { submitDocumentForAnalysis } from "@/services/analyze_document_client";
import {
  AnalyzeDocumentApiResponse,
  SupportedLanguage,
  VoiceGender,
} from "@/types/prescription_report_types";

export default function MedSaathiHomePage() {
  const [language, setLanguage] = useState<SupportedLanguage>("Gujarati");
  const [voiceGender, setVoiceGender] = useState<VoiceGender>("female");
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeDocumentApiResponse | null>(null);

  const handleConfirmSanitizedBlob = async (sanitizedBlob: Blob) => {
    setPendingFile(null);
    setIsAnalyzing(true);
    setErrorMessage(null);

    try {
      const response = await submitDocumentForAnalysis(
        sanitizedBlob,
        language,
        voiceGender
      );
      setResult(response);
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error ? err.message : "Something went wrong."
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-100/90">
      <TopPrivacyHeader />

      <main className="flex-1 w-full max-w-md mx-auto px-4 py-5 space-y-4 pb-16">
        <LanguageAndUploadCard
          selectedLanguage={language}
          onSelectLanguage={setLanguage}
          selectedVoiceGender={voiceGender}
          onSelectVoiceGender={setVoiceGender}
          onFileSelected={(file) => {
            const isPdf =
              file.type === "application/pdf" ||
              file.name.toLowerCase().endsWith(".pdf");
            if (isPdf) {
              handleConfirmSanitizedBlob(file);
            } else {
              setPendingFile(file);
            }
          }}
          isAnalyzing={isAnalyzing}
        />

        {pendingFile && (
          <TouchPrivacyRedactorModal
            file={pendingFile}
            onConfirmSanitizedBlob={handleConfirmSanitizedBlob}
            onCancel={() => setPendingFile(null)}
          />
        )}

        {isAnalyzing && (
          <div className="rounded-3xl bg-white border border-slate-200 p-6 text-center shadow-sm space-y-3">
            <Loader2 className="h-8 w-8 text-teal-600 animate-spin mx-auto" />
            <div>
              <p className="text-sm font-bold text-slate-900">
                Scrubbing PII & Decoding Document...
              </p>
              <p className="text-xs text-slate-500 mt-1">
                Processing pages, matching Jan Aushadhi generic salts & generating {language} voice note
              </p>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="rounded-2xl bg-rose-50 border border-rose-200 p-4 flex items-start gap-2.5 text-xs text-rose-900">
            <ShieldAlert className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        {result && !isAnalyzing && (
          <div className="space-y-4 animate-in fade-in duration-300">
            <RedactedProofPreview
              redactedImageDataUrl={result.redacted_image_data_url}
              redactedPages={result.redacted_pages}
            />

            <GrandparentVoicePlayerCard
              report={result.report}
              audioDataUrl={result.audio_data_url}
              language={language}
              initialVoiceGender={voiceGender}
            />

            <VisualPillScheduleCard
              medicines={result.report.medicines}
              icsCalendarText={result.ics_calendar_text}
            />

            <JanAushadhiSavingsCard
              savingsList={result.report.generic_savings}
              totalMonthlySavingsInr={result.report.total_monthly_savings_inr}
            />

            <LabAndDoctorQuestionsCard
              labAbnormalities={result.report.lab_abnormalities_summary}
              doctorQuestions={result.report.doctor_questions}
            />
          </div>
        )}
      </main>
    </div>
  );
}
