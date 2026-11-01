import {
  getAnalyzeDocumentEndpoint,
  getGenerateVoiceEndpoint,
} from "@/config/api_endpoints";
import {
  AnalyzeDocumentApiResponse,
  SupportedLanguage,
  VoiceGender,
} from "@/types/prescription_report_types";

/** Safely extracts binary ArrayBuffer and checks magic bytes (resilient to mobile cloud streams). */
async function safelyBufferFile(
  fileBlob: Blob
): Promise<{ buffer: ArrayBuffer; isPdf: boolean }> {
  let arrayBuf: ArrayBuffer;
  try {
    if (typeof fileBlob.arrayBuffer === "function") {
      arrayBuf = await fileBlob.arrayBuffer();
    } else {
      arrayBuf = await new Promise<ArrayBuffer>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as ArrayBuffer);
        reader.onerror = () =>
          reject(reader.error || new Error("Failed to read file"));
        reader.readAsArrayBuffer(fileBlob);
      });
    }
  } catch (err) {
    console.error("Cloud file read error:", err);
    throw new Error(
      "Unable to read the document from cloud storage. If uploading from Google Drive, please ensure the file is saved offline or downloaded to your device first."
    );
  }

  // Detect PDF binary signature (%PDF) anywhere in the first 1KB
  const headerBytes = new Uint8Array(arrayBuf.slice(0, 1024));
  let isPdf = false;
  for (let i = 0; i < headerBytes.length - 4; i++) {
    if (
      headerBytes[i] === 0x25 && // %
      headerBytes[i + 1] === 0x50 && // P
      headerBytes[i + 2] === 0x44 && // D
      headerBytes[i + 3] === 0x46 // F
    ) {
      isPdf = true;
      break;
    }
  }

  if (!isPdf) {
    isPdf =
      fileBlob.type === "application/pdf" ||
      fileBlob.type === "application/x-pdf" ||
      (fileBlob instanceof File &&
        fileBlob.name.toLowerCase().endsWith(".pdf"));
  }

  return { buffer: arrayBuf, isPdf };
}

/** Sends the privacy-scrubbed image blob or PDF, language, and voice gender to FastAPI. */
export async function submitDocumentForAnalysis(
  imageBlob: Blob,
  language: SupportedLanguage,
  voiceGender: VoiceGender = "female"
): Promise<AnalyzeDocumentApiResponse> {
  // Check file size limit (max 15MB to prevent mobile timeouts on cloud free tiers)
  if (imageBlob.size > 15 * 1024 * 1024) {
    throw new Error(
      "The selected document is over 15MB. Please upload a smaller document or snap photos of the prescription."
    );
  }

  // Safely buffer into memory & detect true binary type (critical for Google Drive mobile streams)
  const { buffer, isPdf } = await safelyBufferFile(imageBlob);

  const cleanBlob = new Blob([buffer], {
    type: isPdf ? "application/pdf" : (imageBlob.type || "image/jpeg"),
  });
  const safeFilename = isPdf
    ? "prescription_document.pdf"
    : "sanitized_document.jpg";

  const formData = new FormData();
  formData.append("file", cleanBlob, safeFilename);
  formData.append("language", language);
  formData.append("voice_gender", voiceGender);

  const endpoint = getAnalyzeDocumentEndpoint();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 90000);

  let response: Response;
  try {
    response = await fetch(endpoint, {
      method: "POST",
      body: formData,
      signal: controller.signal,
    });
  } catch (err: unknown) {
    clearTimeout(timeoutId);
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
    if (err instanceof Error && err.name === "AbortError") {
      throw new Error(
        "Analysis timed out after 90 seconds. Please retry or upload a smaller file."
      );
    }
    throw new Error(
      `Failed to connect to backend (${endpoint}). If hosted on Render free tier, the instance may be spinning up—please wait 30 seconds and retry. [Details: ${errorMsg}]`
    );
  } finally {
    clearTimeout(timeoutId);
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
