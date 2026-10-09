import logging
import sys
import os
from fastapi import APIRouter, HTTPException, Request
from api.models.request import IngestRequest
from api.models.response import IngestResponse

# RAG-Ingestion sits beside api/ under RAG-codebase/.
sys.path.append(
    os.path.join(os.path.dirname(__file__), "../../RAG-Ingestion")
)
from run_ingestion import run_ingestion

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: Request, body: IngestRequest):
    logger.info(
        "ingest_received",
        extra={
            "s3_key": body.s3_key,
            "document_id": body.document_id
        }
    )

    try:
        run_ingestion(
            s3_key=body.s3_key,
            document_id=body.document_id
        )
    except Exception as e:
        logger.error("ingestion_error", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    logger.info("ingest_complete", extra={"document_id": body.document_id})

    return IngestResponse(
        status="success",
        document_id=body.document_id,
        message=f"Document {body.document_id} ingested successfully"
    )