"""
OpenAI embedding utilities.
"""
from typing import List
from openai import OpenAI
from config.settings import settings


def get_openai_client() -> OpenAI:
    """Initialize and return OpenAI client."""
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set in environment variables")
    return OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for a list of texts using OpenAI.
    
    Args:
        texts: List of text strings to embed.
        
    Returns:
        List of embedding vectors (each is a list of floats).
    """
    client = get_openai_client()
    
    # OpenAI embeddings API
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts
    )
    
    # Extract embeddings
    embeddings = [item.embedding for item in response.data]
    return embeddings


def embed_text(text: str) -> List[float]:
    """
    Create embedding for a single text.
    
    Args:
        text: Text string to embed.
        
    Returns:
        Embedding vector as a list of floats.
    """
    return embed_texts([text])[0]

