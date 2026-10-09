from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


class IngestRequest(BaseModel):
    s3_key: str | None = None
    document_id: str | None = None
