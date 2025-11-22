"""
RAG (Retrieval-Augmented Generation) logic.
"""
from typing import List, Dict, Any
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from config.settings import settings
from app.embeddings import embed_text, get_openai_client


def get_pinecone_client() -> Pinecone:
    """Initialize and return Pinecone client."""
    if not settings.pinecone_api_key:
        raise ValueError("PINECONE_API_KEY not set in environment variables")
    return Pinecone(api_key=settings.pinecone_api_key)


def ensure_pinecone_index():
    """
    Ensure the Pinecone index exists, create if it doesn't.
    If index exists with wrong dimension, delete and recreate it.
    """
    pc = get_pinecone_client()
    
    # Check if index exists
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    
    if settings.pinecone_index_name not in existing_indexes:
        # Create index if it doesn't exist
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.pinecone_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"  # Adjust region as needed
            )
        )
        print(f"Created Pinecone index: {settings.pinecone_index_name}")
    else:
        # Try to check dimension by attempting to query with a test vector
        # If it fails with dimension mismatch, delete and recreate
        try:
            index = pc.Index(settings.pinecone_index_name)
            # Try a test query with correct dimension to see if it works
            test_vector = [0.0] * settings.pinecone_dimension
            index.query(vector=test_vector, top_k=1)
            print(f"Pinecone index already exists: {settings.pinecone_index_name}")
        except Exception as e:
            error_msg = str(e)
            if "dimension" in error_msg.lower() or "400" in error_msg:
                print(f"Index {settings.pinecone_index_name} has wrong dimension. Deleting and recreating...")
                pc.delete_index(settings.pinecone_index_name)
                # Wait a bit for deletion to complete
                import time
                time.sleep(3)
                pc.create_index(
                    name=settings.pinecone_index_name,
                    dimension=settings.pinecone_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                print(f"Recreated Pinecone index: {settings.pinecone_index_name} with dimension {settings.pinecone_dimension}")
            else:
                print(f"Pinecone index already exists: {settings.pinecone_index_name}")
                raise


def query_pinecone(query_embedding: List[float], top_k: int = None) -> List[Dict[str, Any]]:
    """
    Query Pinecone for similar chunks.
    
    Args:
        query_embedding: Embedding vector of the query.
        top_k: Number of results to return.
        
    Returns:
        List of matching chunks with metadata.
    """
    if top_k is None:
        top_k = settings.top_k
    
    pc = get_pinecone_client()
    index = pc.Index(settings.pinecone_index_name)
    
    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    
    # Format results
    chunks = []
    for match in results.matches:
        chunks.append({
            'id': match.id,
            'score': match.score,
            'text': match.metadata.get('text', ''),
            'page': match.metadata.get('page', 0),
            'metadata': match.metadata
        })
    
    return chunks


def answer_question(question: str) -> Dict[str, Any]:
    """
    Answer a question using RAG flow:
    1. Create embedding for the question
    2. Query Pinecone for top-k similar chunks
    3. Build context from retrieved chunks
    4. Call OpenAI LLM with context
    5. Return answer and sources
    
    Args:
        question: User's question about the CV.
        
    Returns:
        Dictionary with 'answer', 'sources', and 'chunks' keys.
    """
    # Step 1: Create embedding for the question
    question_embedding = embed_text(question)
    
    # Step 2: Query Pinecone for similar chunks
    retrieved_chunks = query_pinecone(question_embedding)
    
    if not retrieved_chunks:
        return {
            'answer': "I couldn't find relevant information in the CV to answer your question.",
            'sources': [],
            'chunks': []
        }
    
    # Step 3: Build context string
    context_parts = []
    for chunk in retrieved_chunks:
        context_parts.append(f"[Page {chunk['page']}]: {chunk['text']}")
    context = "\n\n".join(context_parts)
    
    # Step 4: Build prompt for LLM
    system_prompt = """You are a helpful assistant that answers questions about a CV/resume. 
You must answer questions ONLY using the provided context from the CV. 
Be concise, factual, and professional. 
If the context doesn't contain enough information to answer the question, say so clearly.
Do not make up information that isn't in the provided context."""
    
    user_prompt = f"""Context from CV:
{context}

Question: {question}

Answer the question based only on the context provided above."""
    
    # Step 5: Call OpenAI chat completion
    client = get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,  # Lower temperature for more factual responses
        max_tokens=500
    )
    
    answer = response.choices[0].message.content
    
    # Step 6: Return answer with sources
    return {
        'answer': answer,
        'sources': [{'page': chunk['page'], 'score': chunk['score']} for chunk in retrieved_chunks],
        'chunks': retrieved_chunks
    }

