from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str


class IngestResponse(BaseModel):
    status: str
    document_id: str | None = None
    message: str


class Source(BaseModel):
    document: str
    chunk: str
    page: int | None = None
    similarity: float


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[Source]
