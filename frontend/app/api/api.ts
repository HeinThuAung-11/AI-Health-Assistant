const API_BASE = "http://0.0.0.0:8000";

// Upload PDF file
export const uploadReport = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  console.log("Uploading file:", file.name);
  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error("File upload failed");
  return res.json();
};

// Analyze uploaded report
export const analyzeReportAPI = async (reportId) => {
  console.log("Analyzing report with ID:", reportId);
  const res = await fetch(`${API_BASE}/api/analyze/${reportId}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Analysis failed");
  return res.json();
};

// Ask a question
export const askQuestionAPI = async (reportId, question) => {
  const res = await fetch(`${API_BASE}/api/ask`, {
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
export const getReportAPI = async (reportId) => {
  const res = await fetch(`${API_BASE}/api/report/${reportId}`);
  if (!res.ok) throw new Error("Report not found");
  return res.json();
};
