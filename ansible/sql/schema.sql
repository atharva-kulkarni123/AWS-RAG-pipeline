CREATE EXTENSION IF NOT EXISTS vector;

SELECT extname
FROM pg_extension
WHERE extname = 'vector';

CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    source TEXT,
    page_number INT
);

CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
ON document_chunks
USING hnsw (embedding vector_cosine_ops);