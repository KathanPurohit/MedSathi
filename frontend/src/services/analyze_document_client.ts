import {
  getAnalyzeDocumentEndpoint,
  getGenerateVoiceEndpoint,
} from "@/config/api_endpoints";
import {
  AnalyzeDocumentApiResponse,
  SupportedLanguage,
  VoiceGender,
} from "@/types/prescription_report_types";

/** Sends the privacy-scrubbed image blob or PDF, language, and voice gender to FastAPI. */
export async function submitDocumentForAnalysis(
  imageBlob: Blob,
  language: SupportedLanguage,
  voiceGender: VoiceGender = "female"
): Promise<AnalyzeDocumentApiResponse> {
  const isPdf =
    imageBlob.type === "application/pdf" ||
    (imageBlob instanceof File && imageBlob.name.toLowerCase().endsWith(".pdf"));

  const filename =
    imageBlob instanceof File
      ? imageBlob.name
      : isPdf
      ? "document.pdf"
      : "sanitized-document.jpg";

  const formData = new FormData();
  formData.append("file", imageBlob, filename);
  formData.append("language", language);
  formData.append("voice_gender", voiceGender);

  const endpoint = getAnalyzeDocumentEndpoint();

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    if (
      typeof window !== "undefined" &&
      window.location.hostname !== "localhost" &&
      endpoint.includes("localhost")
    ) {
      throw new Error(
        "Backend URL is missing in production. Please set NEXT_PUBLIC_FASTAPI_BASE_URL in your Vercel Project Settings to your deployed Render URL (https://medsathi-backend.onrender.com)."
      );
    }
    throw new Error(
      `Failed to connect to backend (${endpoint}). If hosted on Render free tier, the instance may be spinning up—please wait 30 seconds and retry. [Details: ${errorMsg}]`
    );
  }

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

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        voice_script: voiceScript,
        language,
        voice_gender: voiceGender,
      }),
    });
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err);
    throw new Error(
      `Failed to connect to backend (${endpoint}) for voice generation: ${errorMsg}`
    );
  }

  if (!response.ok) {
    throw new Error("Failed to generate voice note.");
  }

  const data = await response.json();
  return data.audio_data_url;
}
