// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const API_ENDPOINTS = {
  upload: "/api/upload",
  analyze: (reportId) => `/api/analyze/${reportId}`,
  ask: "/api/ask",
  getReport: (reportId) => `/api/report/${reportId}`,
  deleteReport: (reportId) => `/api/report/${reportId}`,
  listReports: "/api/reports",
  health: "/health",
};

// Helper function for API calls
export const apiCall = async (endpoint, options = {}) => {
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
      const error = await response.json().catch(() => ({
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
export const checkBackendHealth = async () => {
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
