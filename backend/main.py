
"""
Health Navigator API
Main FastAPI application
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import uuid
from typing import Dict
import os

from config import get_settings, get_ai_config
from models.schemas import (
    AnalysisResult, QuestionRequest, QuestionResponse,
    UploadResponse, ErrorResponse, ReportStatus
)
from services.pdf_processor import PDFProcessor
from services.ai_analyzer import HealthReportAnalyzer
from services.vector_store import VectorStoreManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global settings
settings = get_settings()

# Global services (initialized on startup)
pdf_processor: PDFProcessor = None
ai_analyzer: HealthReportAnalyzer = None
vector_manager: VectorStoreManager = None

# In-memory storage (replace with database in production)
report_storage: Dict[str, Dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup, cleanup on shutdown"""
    global pdf_processor, ai_analyzer, vector_manager
    
    logger.info("🚀 Starting Health Navigator API...")
    
    # Initialize services
    pdf_processor = PDFProcessor(
        temp_dir=settings.temp_dir,
        upload_dir=settings.upload_dir
    )
    
    ai_config = get_ai_config()
    ai_analyzer = HealthReportAnalyzer(
        api_key=ai_config['api_key'],
        model=ai_config['model'],
        temperature=ai_config['temperature'],
        max_tokens=ai_config['max_tokens'],
        use_groq=(ai_config['provider'] == 'groq')
    )
    
    vector_manager = VectorStoreManager(
        api_key=ai_config['api_key'],
        use_groq=(ai_config['provider'] == 'groq')
    )
    
    logger.info("✅ All services initialized")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Health Navigator API",
    description="AI-powered health report analysis and Q&A system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ROUTES ====================

@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "message": "Health Navigator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "upload": "POST /api/upload",
            "analyze": "POST /api/analyze/{report_id}",
            "ask": "POST /api/ask",
            "get_report": "GET /api/report/{report_id}",
            "delete_report": "DELETE /api/report/{report_id}",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "pdf_processor": pdf_processor is not None,
            "ai_analyzer": ai_analyzer is not None,
            "vector_manager": vector_manager is not None,
        }
    }


@app.post("/api/upload", response_model=UploadResponse)
async def upload_report(file: UploadFile = File(...)):
    """
    Upload a health report PDF
    
    - **file**: PDF file to upload
    
    Returns report_id for subsequent operations
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed"
            )
        
        # Read file
        content = await file.read()
        file_size = len(content)
        
        # Check file size
        if file_size > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {settings.max_file_size / 1024 / 1024}MB"
            )
        
        # Generate unique report ID
        report_id = str(uuid.uuid4())
        
        # Save file
        file_id, temp_path = pdf_processor.save_upload(content, file.filename)
        
        # Store in memory
        report_storage[report_id] = {
            "report_id": report_id,
            "file_id": file_id,
            "filename": file.filename,
            "file_size": file_size,
            "temp_path": temp_path,
            "status": "uploaded",
            "message": "File uploaded successfully"
        }
        
        logger.info(f"✅ Uploaded report {report_id}: {file.filename} ({file_size} bytes)")
        
        return UploadResponse(
            report_id=report_id,
            filename=file.filename,
            file_size=file_size,
            message="File uploaded successfully. Use /api/analyze/{report_id} to analyze.",
            status="uploaded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/analyze/{report_id}", response_model=AnalysisResult)
async def analyze_report(report_id: str, background_tasks: BackgroundTasks):
    """
    Analyze an uploaded health report
    
    - **report_id**: ID returned from /api/upload
    
    Returns detailed analysis of the health report
    """
    try:
        # Check if report exists
        if report_id not in report_storage:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report_info = report_storage[report_id]
        
        # Check if already analyzed
        if report_info.get("status") == "analyzed":
            logger.info(f"Returning cached analysis for {report_id}")
            return AnalysisResult(**report_info["analysis"])
        
        temp_path = report_info["temp_path"]
        
        # Update status
        report_storage[report_id]["status"] = "processing"
        
        # Step 1: Extract data from PDF
        logger.info(f"📄 Extracting data from {report_id}...")
        extracted_data = pdf_processor.process_health_report(temp_path)
        
        # Step 2: Analyze with AI
        logger.info(f"🤖 Analyzing report {report_id}...")
        analysis_result = ai_analyzer.analyze_report(extracted_data)
        
        # Add report_id
        analysis_result["report_id"] = report_id
        
        # Step 3: Create vector store for Q&A
        logger.info(f"🔍 Creating vector store for {report_id}...")
        vector_manager.create_report_vectorstore(
            report_id=report_id,
            report_text=extracted_data["raw_text"],
            metadata={
                "filename": report_info["filename"],
                "report_type": analysis_result.get("report_type", "Unknown")
            }
        )
        
        # Update storage
        report_storage[report_id].update({
            "status": "analyzed",
            "analysis": analysis_result,
            "extracted_data": extracted_data
        })
        
        # Schedule cleanup of temp file
        background_tasks.add_task(pdf_processor.cleanup, temp_path)
        
        logger.info(f"✅ Successfully analyzed report {report_id}")
        
        return AnalysisResult(**analysis_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        if report_id in report_storage:
            report_storage[report_id]["status"] = "error"
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Ask a question about a health report
    
    - **report_id**: ID of the analyzed report
    - **question**: Question to ask
    - **conversation_history**: Optional previous messages
    
    Returns an AI-generated answer based on the report
    """
    try:
        # Check if report exists
        if request.report_id not in report_storage:
            raise HTTPException(status_code=404, detail="Report not found")
        
        report_info = report_storage[request.report_id]
        
        # Check if analyzed
        if report_info["status"] != "analyzed":
            raise HTTPException(
                status_code=400,
                detail="Report not yet analyzed. Call /api/analyze/{report_id} first."
            )
        
        # Search vector store for relevant context
        logger.info(f"🔍 Searching for context: {request.question[:50]}...")
        similar_chunks = vector_manager.search_similar(
            report_id=request.report_id,
            query=request.question,
            k=3
        )
        
        # Build context from similar chunks
        context = "\n\n".join([chunk["text"] for chunk in similar_chunks])
        
        # Get answer from AI
        logger.info(f"🤖 Generating answer...")
        response = ai_analyzer.answer_question(
            question=request.question,
            report_context=context,
            conversation_history=request.conversation_history
        )
        
        # Add sources
        sources = [f"Section {chunk['chunk_index'] + 1}" for chunk in similar_chunks]
        
        logger.info(f"✅ Question answered for report {request.report_id}")
        
        return QuestionResponse(
            answer=response["answer"],
            confidence=response["confidence"],
            timestamp=response["timestamp"],
            sources=sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Question answering error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


@app.get("/api/report/{report_id}")
async def get_report(report_id: str):
    """
    Get report information and analysis
    
    - **report_id**: ID of the report
    
    Returns report status and analysis if available
    """
    if report_id not in report_storage:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report_info = report_storage[report_id]
    
    # Return different info based on status
    if report_info["status"] == "analyzed":
        return {
            "report_id": report_id,
            "status": report_info["status"],
            "filename": report_info["filename"],
            "analysis": report_info["analysis"]
        }
    else:
        return {
            "report_id": report_id,
            "status": report_info["status"],
            "filename": report_info["filename"],
            "message": report_info.get("message", "Processing...")
        }


@app.delete("/api/report/{report_id}")
async def delete_report(report_id: str):
    """
    Delete a report and all associated data
    
    - **report_id**: ID of the report to delete
    
    Removes report from storage and deletes vector store
    """
    if report_id not in report_storage:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        # Delete vector store
        vector_manager.delete_vectorstore(report_id)
        
        # Remove from storage
        del report_storage[report_id]
        
        logger.info(f"🗑️ Deleted report {report_id}")
        
        return {
            "message": "Report deleted successfully",
            "report_id": report_id
        }
    except Exception as e:
        logger.error(f"❌ Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


@app.get("/api/reports")
async def list_reports():
    """
    List all reports
    
    Returns a list of all uploaded reports with their status
    """
    reports = []
    for report_id, info in report_storage.items():
        reports.append({
            "report_id": report_id,
            "filename": info["filename"],
            "status": info["status"],
            "file_size": info["file_size"]
        })
    
    return {
        "total": len(reports),
        "reports": reports
    }


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"❌ Global error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🏥 Starting Health Navigator API...")
    logger.info(f"   Frontend: {settings.frontend_url}")
    logger.info(f"   Debug: {settings.debug}")
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
