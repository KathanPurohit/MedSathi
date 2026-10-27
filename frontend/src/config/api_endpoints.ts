/** Centralizes backend API URLs so components never hardcode endpoints. */
export const getFastApiBaseUrl = (): string => {
  if (typeof window !== "undefined") {
    // If opened on phone/tablet over local network, point to PC's IP port 8000
    const host = window.location.hostname;
    if (host && host !== "localhost" && host !== "127.0.0.1") {
      return `http://${host}:8000`;
    }
  }
  return process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || "http://localhost:8000";
};

export const FASTAPI_BASE_URL = getFastApiBaseUrl();

export const getAnalyzeDocumentEndpoint = (): string => {
  return `${getFastApiBaseUrl()}/api/analyze-document`;
};

export const getGenerateVoiceEndpoint = (): string => {
  return `${getFastApiBaseUrl()}/api/generate-voice`;
};

export const ANALYZE_DOCUMENT_ENDPOINT = `${FASTAPI_BASE_URL}/api/analyze-document`;
