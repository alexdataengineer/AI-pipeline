"""
Configuration settings for the RAG pipeline.
Loads from environment variables with sensible defaults.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    
    # Pinecone Configuration
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "alex_cv_index")
    pinecone_dimension: int = int(os.getenv("PINECONE_DIMENSION", "1536"))  # text-embedding-3-small dimension
    
    # PDF Configuration
    cv_pdf_path: str = os.getenv("CV_PDF_PATH", "/Users/alexsandersilveira/Downloads/cv/Profile (6).pdf")
    
    # Chunking Configuration
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "100"))
    
    # RAG Configuration
    top_k: int = int(os.getenv("TOP_K", "3"))  # Number of chunks to retrieve
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

