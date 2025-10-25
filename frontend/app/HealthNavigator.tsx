"use client";
// import { MockReport } from "@/utli-types";
import {
  AlertCircle,
  Calendar,
  CheckCircle,
  DollarSign,
  FileText,
  Loader2,
  MessageSquare,
  Pill,
  Upload,
} from "lucide-react";
import { useState } from "react";
import { analyzeReportAPI, askQuestionAPI, uploadReport } from "./api/api";
import BackendStatusChecker from "./components/BackendStatus";

// Types
interface KeyFinding {
  metric: string;
  range: string;
  value: string;
  status: "elevated" | "low" | "normal";
}

interface Report {
  patientName: string;
  reportType: string;
  date: string;
  keyFindings: KeyFinding[];
  summary: string;
  nextSteps: string[];
  urgency: string;
  reportId: string;
}

interface ChatMessage {
  type: "user" | "ai";
  text: string;
}

const HealthNavigator = () => {
  const [activeTab, setActiveTab] = useState<string>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [report, setReport] = useState<Report | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [userQuestion, setUserQuestion] = useState<string>("");

  const analyzeReport = async (): Promise<void> => {
    if (!file) return alert("Please upload a file first.");
    try {
      setAnalyzing(true);
      setReport(null);
      console.log("Starting analysis for file:", file.name);

      // Step 1: Upload PDF
      const uploadRes = await uploadReport(file);
      const reportId = uploadRes.report_id;
      console.log("Uploaded Report ID:", reportId);

      // Step 2: Analyze uploaded report
      const analysisRes = await analyzeReportAPI(reportId);
      console.log("Analysis Result:", analysisRes);

      // Step 3: Set result to display
      setReport({
        patientName: analysisRes.patient_name || "Unknown",
        reportType: analysisRes.report_type || "Unknown Report",
        date: new Date().toISOString().split("T")[0],
        keyFindings: analysisRes.key_findings || [],
        summary: analysisRes.summary || "No summary available.",
        nextSteps: analysisRes.next_steps || [],
        urgency: analysisRes.urgency || "routine",
        reportId,
      });

      setActiveTab("results");
    } catch (err) {
      console.error(err);
      alert("Error analyzing report: " + (err as Error).message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const uploadedFile = e.target.files?.[0];
    console.log("Selected file:", uploadedFile);
    if (uploadedFile && uploadedFile.type === "application/pdf") {
      setFile(uploadedFile);
    } else {
      alert("Please upload a PDF file");
    }
  };

  const handleAskQuestion = async (): Promise<void> => {
    if (!userQuestion.trim()) return;
    if (!report?.reportId) return alert("No analyzed report found.");

    // Add user question to chat
    const newMessages: ChatMessage[] = [...chatMessages, { type: "user", text: userQuestion }];
    setChatMessages(newMessages);
    setUserQuestion("");

    try {
      const response = await askQuestionAPI(report.reportId, userQuestion);
      const aiResponse = response.answer || "No answer available.";

      setChatMessages([...newMessages, { type: "ai", text: aiResponse }]);
    } catch (err) {
      console.error(err);
      setChatMessages([...newMessages, { type: "ai", text: "Sorry, something went wrong." }]);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50">
      <BackendStatusChecker />
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Health Navigator</h1>
              <p className="text-sm text-gray-600">Understand your health reports, simplified</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 bg-white rounded-lg p-1 shadow-sm">
          <button
            onClick={() => setActiveTab("upload")}
            className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
              activeTab === "upload" ? "bg-blue-500 text-white shadow-md" : "text-gray-600 hover:bg-gray-50"
            }`}>
            <Upload className="w-5 h-5 inline-block mr-2" />
            Upload Report
          </button>
          <button
            onClick={() => setActiveTab("results")}
            disabled={!report}
            className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
              activeTab === "results"
                ? "bg-blue-500 text-white shadow-md"
                : report
                ? "text-gray-600 hover:bg-gray-50"
                : "text-gray-400 cursor-not-allowed"
            }`}>
            <FileText className="w-5 h-5 inline-block mr-2" />
            Results
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            disabled={!report}
            className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
              activeTab === "chat"
                ? "bg-blue-500 text-white shadow-md"
                : report
                ? "text-gray-600 hover:bg-gray-50"
                : "text-gray-400 cursor-not-allowed"
            }`}>
            <MessageSquare className="w-5 h-5 inline-block mr-2" />
            Ask Questions
          </button>
          <button
            onClick={() => setActiveTab("actions")}
            disabled={!report}
            className={`flex-1 py-3 px-4 rounded-md font-medium transition-all ${
              activeTab === "actions"
                ? "bg-blue-500 text-white shadow-md"
                : report
                ? "text-gray-600 hover:bg-gray-50"
                : "text-gray-400 cursor-not-allowed"
            }`}>
            <Calendar className="w-5 h-5 inline-block mr-2" />
            Next Steps
          </button>
        </div>

        {/* Upload Tab */}
        {activeTab === "upload" && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Health Report</h2>
              <p className="text-gray-600">We support PDF lab reports, test results, and medical documents</p>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                accept="application/pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">Click to upload or drag and drop</p>
                <p className="text-sm text-gray-500">PDF files only (Max 10MB)</p>
              </label>
            </div>

            {file && (
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText className="w-8 h-8 text-blue-600" />
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-600">{(file.size / 1024).toFixed(2)} KB</p>
                    </div>
                  </div>
                  <button
                    onClick={analyzeReport}
                    disabled={analyzing}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2">
                    {analyzing ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Analyzing...
                      </>
                    ) : (
                      "Analyze Report"
                    )}
                  </button>
                </div>
              </div>
            )}

            <div className="mt-8 grid grid-cols-3 gap-4 text-center">
              <div className="p-4 bg-gray-50 rounded-lg">
                <AlertCircle className="w-8 h-8 mx-auto text-blue-500 mb-2" />
                <p className="text-sm font-medium text-gray-700">Secure & Private</p>
                <p className="text-xs text-gray-500 mt-1">Your data is encrypted</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <CheckCircle className="w-8 h-8 mx-auto text-green-500 mb-2" />
                <p className="text-sm font-medium text-gray-700">AI-Powered</p>
                <p className="text-xs text-gray-500 mt-1">Advanced analysis</p>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <MessageSquare className="w-8 h-8 mx-auto text-purple-500 mb-2" />
                <p className="text-sm font-medium text-gray-700">Ask Anything</p>
                <p className="text-xs text-gray-500 mt-1">Get instant answers</p>
              </div>
            </div>
          </div>
        )}

        {/* Results Tab */}
        {activeTab === "results" && report && (
          <div className="space-y-6">
            {/* Summary Card */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{report.reportType}</h2>
                  <p className="text-gray-600">Date: {report.date}</p>
                </div>
                <span
                  className={`px-4 py-2 rounded-full text-sm font-medium ${
                    report.urgency === "urgent"
                      ? "bg-red-100 text-red-700"
                      : report.urgency === "moderate"
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-green-100 text-green-700"
                  }`}>
                  {report.urgency === "urgent" ? "Urgent" : report.urgency === "moderate" ? "Moderate" : "Routine"}
                </span>
              </div>

              <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                <h3 className="font-semibold text-gray-900 mb-2">Summary in Plain English:</h3>
                <p className="text-gray-700">{report.summary}</p>
              </div>
            </div>

            {/* Detailed Findings */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">Detailed Results</h3>
              <div className="space-y-3">
                {report.keyFindings.map((finding, idx) => (
                  <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{finding.metric}</p>
                      <p className="text-sm text-gray-600">Normal range: {finding.range}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-lg text-gray-900">{finding.value}</p>
                      <span
                        className={`text-sm font-medium ${
                          finding.status === "elevated" || finding.status === "low"
                            ? "text-yellow-600"
                            : "text-green-600"
                        }`}>
                        {finding.status.charAt(0).toUpperCase() + finding.status.slice(1)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Chat Tab */}
        {activeTab === "chat" && report && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Ask Questions About Your Report</h2>

            <div className="h-96 overflow-y-auto mb-4 p-4 bg-gray-50 rounded-lg">
              {chatMessages.length === 0 ? (
                <div className="text-center text-gray-500 mt-16">
                  <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-lg font-medium">Ask me anything about your report</p>
                  <p className="text-sm mt-2">I'll explain it in simple terms</p>
                </div>
              ) : (
                <div className="space-y-4 text-black">
                  {chatMessages.map((msg, idx) => (
                    <div key={idx} className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-md p-3 rounded-lg ${
                          msg.type === "user" ? "bg-blue-500 text-white" : "bg-white border border-gray-200"
                        }`}>
                        <p className="text-sm">{msg.text}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={userQuestion}
                onChange={(e) => setUserQuestion(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleAskQuestion()}
                placeholder="Type your question..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
              />
              <button
                onClick={handleAskQuestion}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors">
                Send
              </button>
            </div>
          </div>
        )}

        {/* Actions Tab */}
        {activeTab === "actions" && report && (
          <div className="space-y-6">
            {/* Next Steps */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Recommended Next Steps</h2>
              <div className="space-y-3">
                {report.nextSteps.map((step, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                    <CheckCircle className="w-5 h-5 text-green-500 mt-1 flex-shrink-0" />
                    <p className="text-gray-700">{step}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="grid md:grid-cols-3 gap-4">
              <button className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow text-left">
                <Calendar className="w-10 h-10 text-blue-500 mb-3" />
                <h3 className="font-bold text-gray-900 mb-2">Book Appointment</h3>
                <p className="text-sm text-gray-600">Schedule a follow-up with your doctor</p>
              </button>

              <button className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow text-left">
                <DollarSign className="w-10 h-10 text-green-500 mb-3" />
                <h3 className="font-bold text-gray-900 mb-2">Find Affordable Care</h3>
                <p className="text-sm text-gray-600">Explore cost-effective options near you</p>
              </button>

              <button className="p-6 bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow text-left">
                <Pill className="w-10 h-10 text-purple-500 mb-3" />
                <h3 className="font-bold text-gray-900 mb-2">Track Medications</h3>
                <p className="text-sm text-gray-600">Set reminders and manage prescriptions</p>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="max-w-6xl mx-auto px-4 py-6 text-center text-sm text-gray-600">
        <div className="flex items-center justify-center gap-2 mb-2">
          <AlertCircle className="w-4 h-4" />
          <p className="font-medium">Important: This tool is for educational purposes only</p>
        </div>
        <p>Always consult with healthcare professionals for medical advice and treatment decisions.</p>
      </div>
    </div>
  );
};

export default HealthNavigator;
