from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SearchRequest(BaseModel):
    query: str
    organization_id: Optional[str] = None
    document_id: Optional[str] = None
    top_k: int = 5

class SearchResult(BaseModel):
    text: str
    score: float
    relevance: str
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: Optional[float] = None