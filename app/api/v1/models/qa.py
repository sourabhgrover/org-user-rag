from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class QARequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Question to ask")
    # organization_id: Optional[str] = Field(None, description="Organization ID to search in")
    document_id: Optional[str] = Field(None, description="Specific document to search in") 
    max_context_chunks: int = Field(5, ge=1, le=10, description="Number of context chunks to use")

class ContextSource(BaseModel):
    text: str
    score: float
    metadata: Dict[str, Any]

class QAResponse(BaseModel):
    question: str
    answer: str
    confidence: str  # High, Medium, Low
    context_sources: List[ContextSource]
    total_sources: int
    response_time_ms: Optional[float] = None