"""
FastAPI application exposing a chat endpoint for CV questions.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.rag import answer_question, ensure_pinecone_index

# Initialize FastAPI app
app = FastAPI(
    title="CV RAG Chat API",
    description="Ask questions about the CV using RAG",
    version="1.0.0"
)


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: list
    chunks: Optional[list] = None


@app.on_event("startup")
async def startup_event():
    """Ensure Pinecone index exists on startup."""
    try:
        ensure_pinecone_index()
        print("Pinecone index verified/created successfully")
    except Exception as e:
        print(f"Warning: Could not verify Pinecone index: {e}")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "CV RAG Chat API",
        "endpoints": {
            "/chat": "POST - Ask questions about the CV",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that answers questions about the CV using RAG.
    
    Example request:
    {
        "question": "What is my work experience?"
    }
    """
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    try:
        result = answer_question(request.question)
        return ChatResponse(
            answer=result['answer'],
            sources=result['sources'],
            chunks=result.get('chunks', [])
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

