
"""
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class HealthMetric(BaseModel):
    """Individual health test metric"""
    metric: str
    value: str
    status: Literal["normal", "elevated", "low", "critical"]
    range: str
    unit: Optional[str] = None


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    report_id: str
    patient_name: Optional[str] = None
    report_type: str
    date: Optional[str] = None
    key_findings: List[HealthMetric]
    summary: str
    next_steps: List[str]
    urgency: Literal["routine", "moderate", "urgent"]
    confidence_score: float = Field(ge=0, le=1)
    processed_at: Optional[str] = None
    model_name: Optional[str] = None
    provider: Optional[str] = None


class QuestionRequest(BaseModel):
    """Request to ask a question about a report"""
    report_id: str
    question: str
    conversation_history: Optional[List[dict]] = []


class QuestionResponse(BaseModel):
    """Response to a question"""
    answer: str
    confidence: float
    timestamp: str
    sources: Optional[List[str]] = []


class UploadResponse(BaseModel):
    """Response after uploading a file"""
    report_id: str
    filename: str
    file_size: int
    message: str
    status: str = "uploaded"


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int = 400


class ReportStatus(BaseModel):
    """Report processing status"""
    report_id: str
    status: Literal["uploaded", "processing", "analyzed", "error"]
    message: str
    progress: Optional[int] = None
