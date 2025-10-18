"""
AI Analyzer Service
Supports both OpenAI and Groq for health report analysis
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import both clients
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthReportAnalyzer:
    """
    Analyzes health reports using AI (OpenAI or Groq).
    """
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.3,
        max_tokens: int = 2000,
        use_groq: bool = False
    ):
        """
        Initialize the analyzer.
        
        Args:
            api_key: API key for the provider
            model: Model name to use
            temperature: Creativity level (0.0-1.0)
            max_tokens: Maximum tokens in response
            use_groq: If True, use Groq; otherwise use OpenAI
        """
        self.use_groq = use_groq
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if self.use_groq:
            if not GROQ_AVAILABLE:
                raise ImportError("Groq SDK not installed. Run: pip install groq")
            self.client = Groq(api_key=api_key)
            logger.info(f"✅ AI Analyzer initialized with Groq model: {model}")
        else:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI SDK not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key)
            logger.info(f"✅ AI Analyzer initialized with OpenAI model: {model}")
    
    def analyze_report(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze extracted health report data.
        
        Args:
            extracted_data: Dictionary from PDF processor
            
        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info("Starting report analysis...")
            
            # Prepare data
            raw_text = extracted_data.get("raw_text", "")[:4000]
            medical_values = extracted_data.get("medical_values", [])
            tables = extracted_data.get("tables", [])
            
            # Format medical values
            medical_values_str = self._format_medical_values(medical_values)
            
            # Create prompt
            prompt = self._create_analysis_prompt(
                raw_text=raw_text,
                medical_values=medical_values_str,
                num_tables=len(tables)
            )
            
            # Call API (same interface for both providers!)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert medical AI assistant helping patients understand their health reports."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            analysis_result = self._parse_analysis_response(response_text)
            
            # Add metadata
            analysis_result["processed_at"] = datetime.utcnow().isoformat()
            analysis_result["model_used"] = self.model
            analysis_result["provider"] = "groq" if self.use_groq else "openai"
            
            logger.info(f"✅ Analysis complete: {analysis_result.get('report_type', 'Unknown')}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Error analyzing report: {e}")
            raise
    
    def _create_analysis_prompt(self, raw_text: str, medical_values: str, num_tables: int) -> str:
        """Create the prompt for analyzing health reports"""
        
        return f"""You are an expert medical AI assistant helping patients understand their health reports.

Your task is to analyze this health report and provide a clear, empathetic explanation.

IMPORTANT GUIDELINES:
- Use simple, non-technical language
- Be accurate and factual
- Never diagnose conditions
- Always recommend consulting healthcare professionals
- Be reassuring when appropriate
- Highlight what requires attention

REPORT DATA:
Date: {datetime.now().strftime("%Y-%m-%d")}
Number of tables: {num_tables}

Raw Text:
{raw_text}

Medical Values:
{medical_values}

Please provide a JSON response with this exact structure:
{{
  "report_type": "Type of report (e.g., Complete Blood Count, Metabolic Panel)",
  "patient_name": "Patient name if found, otherwise null",
  "date": "Report date if found, otherwise null",
  "key_findings": [
    {{
      "metric": "Test name",
      "value": "Result value",
      "status": "normal/elevated/low/critical",
      "range": "Reference range",
      "unit": "Unit of measurement"
    }}
  ],
  "summary": "2-3 sentences explaining what the results mean in simple English",
  "next_steps": [
    "Specific action the patient should take",
    "Another specific action",
    "Third action if needed"
  ],
  "urgency": "routine/moderate/urgent",
  "confidence_score": 0.85
}}

URGENCY LEVELS:
- routine: All values normal or minor variations
- moderate: Some concerning values that need follow-up
- urgent: Critical values requiring immediate medical attention

Generate the JSON response now:"""
    
    def _format_medical_values(self, medical_values: List[Dict]) -> str:
        """Format medical values for the prompt"""
        if not medical_values:
            return "No structured medical values extracted."
        
        formatted = []
        for i, value in enumerate(medical_values[:20], 1):
            formatted.append(f"{i}. {json.dumps(value, indent=2)}")
        
        return "\n".join(formatted)
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Find JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                
                # Validate required fields
                required_fields = ["report_type", "key_findings", "summary", "next_steps", "urgency"]
                for field in required_fields:
                    if field not in parsed:
                        logger.warning(f"Missing field: {field}")
                        parsed[field] = self._get_default_value(field)
                
                return parsed
            else:
                raise ValueError("No JSON found in response")
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse JSON: {e}")
            return self._create_fallback_response(response_text)
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for missing fields"""
        defaults = {
            "report_type": "Health Report",
            "patient_name": None,
            "date": None,
            "key_findings": [],
            "summary": "Analysis could not be completed. Please consult your healthcare provider.",
            "next_steps": ["Consult with your healthcare provider about these results"],
            "urgency": "routine",
            "confidence_score": 0.5
        }
        return defaults.get(field)
    
    def _create_fallback_response(self, text: str) -> Dict[str, Any]:
        """Create basic response if JSON parsing fails"""
        return {
            "report_type": "Health Report",
            "patient_name": None,
            "date": None,
            "key_findings": [],
            "summary": text[:500] if text else "Unable to analyze report.",
            "next_steps": ["Consult with your healthcare provider"],
            "urgency": "routine",
            "confidence_score": 0.5
        }
    
    def answer_question(
        self, 
        question: str, 
        report_context: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, str]:
        """Answer questions about a health report"""
        try:
            logger.info(f"Answering question: {question[:100]}...")
            
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful medical AI assistant. Answer questions clearly and accurately."
                }
            ]
            
            # Add conversation history
            if conversation_history:
                for msg in conversation_history[-5:]:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        messages.append({"role": role, "content": content})
            
            # Add current question
            user_message = f"""Report Context:
{report_context}

Question: {question}

Provide a clear, helpful answer:"""
            
            messages.append({"role": "user", "content": user_message})
            
            # Get response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "confidence": 0.85,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": "I apologize, but I encountered an error. Please try rephrasing your question.",
                "confidence": 0.0,
                "timestamp": datetime.utcnow().isoformat()
            }
