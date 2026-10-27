/** Centralizes backend API URLs so components never hardcode endpoints. */
export const FASTAPI_BASE_URL =
  process.env.NEXT_PUBLIC_FASTAPI_BASE_URL || "http://localhost:8000";

export const ANALYZE_DOCUMENT_ENDPOINT = `${FASTAPI_BASE_URL}/api/analyze-document`;
