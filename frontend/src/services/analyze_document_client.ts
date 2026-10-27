import { ANALYZE_DOCUMENT_ENDPOINT } from "@/config/api_endpoints";
import {
  AnalyzeDocumentApiResponse,
  SupportedLanguage,
} from "@/types/prescription_report_types";

/** Sends the privacy-scrubbed image blob and selected language to FastAPI. */
export async function submitDocumentForAnalysis(
  imageBlob: Blob,
  language: SupportedLanguage
): Promise<AnalyzeDocumentApiResponse> {
  const formData = new FormData();
  formData.append("file", imageBlob, "sanitized-document.jpg");
  formData.append("language", language);

  const response = await fetch(ANALYZE_DOCUMENT_ENDPOINT, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to analyze medical document.");
  }

  return response.json();
}
