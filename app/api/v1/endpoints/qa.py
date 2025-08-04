from fastapi import APIRouter , HTTPException
from app.services import rag_service
from app.api.v1.models.qa import QARequest,QAResponse,ContextSource  # Assuming you have a model for the request
import time

router = APIRouter(prefix="/qa", tags=["Q&A"])

@router.post("/ask",response_model=QAResponse)
def ask_quetion(request:QARequest):
    try:
        start_time = time.time()
     # Validate question
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        print(f"Received question: {request.question}")
        
        # Get AI answer with context
        result = rag_service.answer_question(
            question=request.question,
            document_id=request.document_id,
            organization_id=request.organization_id,
            max_context_chunks=request.max_context_chunks
        )
        print(f"AI Answer: {result['answer']}")
        # Calculate response time
        response_time = (time.time() - start_time) * 1000
         # Format context sources
        context_sources = [
            ContextSource(
                text=source["text"],
                score=source["score"],
                metadata=source["metadata"]
            )
            for source in result["context_sources"]
        ]

        return QAResponse(
            question=request.question,
            answer=result["answer"],
            confidence=result["confidence"],
            context_sources=context_sources,
            total_sources=len(context_sources),
            response_time_ms=round(response_time, 2)
        )
    except Exception as e:
        print(f"Hello")
        print(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

# @router.get("/ask/{question}")
# def ask_one(question: str):
#     rag_service.answer_question(question)
#     return {"message": f"This is a placeholder for the Q&A endpoint with question: {question}. Implement your logic here."} 