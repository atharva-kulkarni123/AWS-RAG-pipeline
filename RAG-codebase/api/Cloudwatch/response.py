from pydantic import BaseModel
from typing import List, Optional


class Source(BaseModel):
    document: str
    chunk: str
    page: Optional[int] = None
    similarity: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: List[Source]

    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the refund policy?",
                "answer": "Refunds are processed within 7 business days...",
                "sources": [
                    {
                        "document": "doc-refund-001",
                        "chunk": "chunk-42",
                        "page": 3,
                        "similarity": 0.91
                    }
                ]
            }
        }


class IngestResponse(BaseModel):
    status: str
    document_id: str
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str


class ErrorResponse(BaseModel):
    detail: str