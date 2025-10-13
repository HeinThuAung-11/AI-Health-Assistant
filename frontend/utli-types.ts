export type MockReport = {
  patientName: string;
  reportType: string;
  date: string;
  keyFindings: {
    metric: string;
    value: string;
    status: string;
    range: string;
  }[];
  summary: string;
  nextSteps: string[];
  urgency: string;
};
