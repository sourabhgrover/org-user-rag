from fastapi import APIRouter, HTTPException, Depends
from app.api.v1.models.search import SearchRequest, SearchResponse, SearchResult
from app.services import rag_service , search_service
import time

from app.core.dependencies import get_current_active_user

router = APIRouter(prefix="/search", tags=["Search"],dependencies=[Depends(get_current_active_user)])

@router.post("/", response_model=SearchResponse)
def search_documents(request: SearchRequest):
    """
    Search through uploaded documents using semantic similarity
    """
    try:
        start_time = time.time()
        
        # Validate query
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        print(f"Received search query: {request.query}")
        # One simple call - handles all cases
        results = search_service.search_documents(
            query=request.query,
            document_id=request.document_id,
            organization_id=request.organization_id,
            top_k=request.top_k
        )
        
        # Calculate search time
        search_time = (time.time() - start_time) * 1000
        
        # Format response
        search_results = [
            SearchResult(
                text=result["text"],
                score=result["score"],
                relevance=result["relevance"],
                metadata=result["metadata"]
            )
            for result in results
        ]
        
        return SearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results),
            search_time_ms=round(search_time, 2)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")