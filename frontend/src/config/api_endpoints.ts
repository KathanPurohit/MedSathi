/** Centralizes backend API URLs so components never hardcode endpoints. */
export const getFastApiBaseUrl = (): string => {
  // 1. If explicit environment variable is set (Vercel production or .env.local)
  if (process.env.NEXT_PUBLIC_FASTAPI_BASE_URL) {
    return process.env.NEXT_PUBLIC_FASTAPI_BASE_URL.replace(/\/+$/, "");
  }

  // 2. Client-side LAN debugging (e.g. mobile testing over local WiFi)
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (
      host &&
      host !== "localhost" &&
      host !== "127.0.0.1" &&
      (/^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(host) || host.endsWith(".local"))
    ) {
      return `http://${host}:8000`;
    }
  }

  return "http://localhost:8000";
};

export const FASTAPI_BASE_URL = getFastApiBaseUrl();

export const getAnalyzeDocumentEndpoint = (): string => {
  return `${getFastApiBaseUrl()}/api/analyze-document`;
};

export const getGenerateVoiceEndpoint = (): string => {
  return `${getFastApiBaseUrl()}/api/generate-voice`;
};

export const ANALYZE_DOCUMENT_ENDPOINT = `${FASTAPI_BASE_URL}/api/analyze-document`;
