import {
  getAnalyzeDocumentEndpoint,
  getGenerateVoiceEndpoint,
} from "@/config/api_endpoints";
import {
  AnalyzeDocumentApiResponse,
  SupportedLanguage,
  VoiceGender,
} from "@/types/prescription_report_types";

/** Sends the privacy-scrubbed image blob, language, and voice gender to FastAPI. */
export async function submitDocumentForAnalysis(
  imageBlob: Blob,
  language: SupportedLanguage,
  voiceGender: VoiceGender = "female"
): Promise<AnalyzeDocumentApiResponse> {
  const formData = new FormData();
  formData.append("file", imageBlob, "sanitized-document.jpg");
  formData.append("language", language);
  formData.append("voice_gender", voiceGender);

  const endpoint = getAnalyzeDocumentEndpoint();
  const response = await fetch(endpoint, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to analyze medical document.");
  }

  return response.json();
}

/** Regenerates the voice note on-the-fly when toggling between Female/Male doctor voices. */
export async function generateVoiceNote(
  voiceScript: string,
  language: SupportedLanguage,
  voiceGender: VoiceGender
): Promise<string> {
  const endpoint = getGenerateVoiceEndpoint();
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      voice_script: voiceScript,
      language,
      voice_gender: voiceGender,
    }),
  });

  if (!response.ok) {
    throw new Error("Failed to generate voice note.");
  }

  const data = await response.json();
  return data.audio_data_url;
}
