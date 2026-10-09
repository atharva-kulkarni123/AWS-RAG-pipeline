import logging
from fastapi import APIRouter, HTTPException, Request
from api.models.request import QueryRequest
from api.models.response import QueryResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(request: Request, body: QueryRequest):
    rag_service = request.app.state.rag_service

    logger.info(
        "query_received",
        extra={"question_length": len(body.question)}
    )

    try:
        result = rag_service.answer(body.question)
    except Exception as e:
        logger.error("rag_pipeline_error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="RAG pipeline error")

    logger.info(
        "query_complete",
        extra={"source_count": len(result["sources"])}
    )

    return QueryResponse(
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"]
    )