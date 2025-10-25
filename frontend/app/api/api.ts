export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Types
interface UploadResponse {
  // Add the actual response structure from your API
  reportId: string;
  [key: string]: any;
}

interface AnalysisResponse {
  // Add the actual response structure from your API
  [key: string]: any;
}

interface QuestionResponse {
  // Add the actual response structure from your API
  answer: string;
  [key: string]: any;
}

interface ReportResponse {
  // Add the actual response structure from your API
  [key: string]: any;
}

// Upload PDF file
export const uploadReport = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  console.log("Uploading file:", file.name);
  const res = await fetch(`${API_BASE_URL}/api/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("File upload failed");
  return res.json();
};

// Analyze uploaded report
export const analyzeReportAPI = async (reportId: string): Promise<AnalysisResponse> => {
  console.log("Analyzing report with ID:", reportId);
  const res = await fetch(`${API_BASE_URL}/api/analyze/${reportId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
};

// Ask a question
export const askQuestionAPI = async (reportId: string, question: string): Promise<QuestionResponse> => {
  const res = await fetch(`${API_BASE_URL}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      report_id: reportId,
      question,
    }),
  });
  if (!res.ok) throw new Error("Question failed");
  return res.json();
};

// Get report info
export const getReportAPI = async (reportId: string): Promise<ReportResponse> => {
  const res = await fetch(`${API_BASE_URL}/api/report/${reportId}`);
  if (!res.ok) throw new Error("Report not found");
  return res.json();
};
