// API Configuration
export const API_BASE_URL = "https://ai-health-navigator-api.onrender.com";

export const API_ENDPOINTS = {
  upload: "/api/upload",
  analyze: (reportId: string): string => `/api/analyze/${reportId}`,
  ask: "/api/ask",
  getReport: (reportId: string): string => `/api/report/${reportId}`,
  deleteReport: (reportId: string): string => `/api/report/${reportId}`,
  listReports: "/api/reports",
  health: "/health",
} as const;

// Types
interface ApiCallOptions extends RequestInit {
  headers?: Record<string, string>;
}

interface ApiErrorResponse {
  detail?: string;
  message?: string;
}

// Helper function for API calls
export const apiCall = async <T = any>(endpoint: string, options: ApiCallOptions = {}): Promise<T> => {
  const url = `${API_BASE_URL}${endpoint}`;

  console.log(`🔗 API Call: ${url}`);

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiErrorResponse = await response.json().catch(() => ({
        detail: `HTTP ${response.status}`,
      }));
      throw new Error(error.detail || error.message || "Request failed");
    }

    return await response.json();
  } catch (error) {
    console.error("❌ API Error:", error);
    throw error;
  }
};

// Check if backend is awake (for cold starts)
export const checkBackendHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: AbortSignal.timeout(60000), // 60 second timeout for cold start
    });
    return response.ok;
  } catch (error) {
    console.error("Backend health check failed:", error);
    return false;
  }
};
