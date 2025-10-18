# config.py
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # API Keys
    openai_api_key: Optional[str] = ""
    groq_api_key: Optional[str] = ""
    pinecone_api_key: Optional[str] = ""
    pinecone_environment: Optional[str] = ""
    
    # AI Provider Selection
    use_groq: bool = False  # Set to True to use Groq instead of OpenAI
    
    # App Config
    app_name: str = "Health Navigator API"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # File Upload
    max_file_size: int = 10485760
    allowed_extensions: str = "pdf"
    upload_dir: str = "uploads"
    temp_dir: str = "temp"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Vector Store
    vector_store_type: str = "faiss"
    embedding_model: str = "text-embedding-ada-002"
    
    # LLM Configuration
    llm_model: str = "gpt-3.5-turbo"  # Used for OpenAI
    groq_model: str = "llama-3.3-70b-versatile"  # Used for Groq
    llm_temperature: float = 0.3
    max_tokens: int = 2000
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

def get_ai_config():
    """Helper function to get the right AI configuration"""
    settings = get_settings()
    
    if settings.use_groq:
        return {
            "provider": "groq",
            "api_key": settings.groq_api_key,
            "model": settings.groq_model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.max_tokens
        }
    else:
        return {
            "provider": "openai",
            "api_key": settings.openai_api_key,
            "model": settings.llm_model,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.max_tokens
        }