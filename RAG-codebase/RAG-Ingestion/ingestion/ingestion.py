from s3_client import S3Client
from pdf_processor import PDFProcessor
from ingestion.chunker import Chunker
from embedding.embedding import EmbeddingService
from vectorstore.vectordb import VectorDB
from config import Config

class IngestionService:

    def __init__(self):
        self.s3 = S3Client()
        self.pdf_processor = PDFProcessor()
        self.chunker = Chunker()
        self.embedding_service = EmbeddingService()
        self.vector_db = VectorDB()

    def ingest(self, s3_key=None, document_id=None):
        files = (
            [s3_key]
            if s3_key
            else self.s3.list_files(Config.S3_BUCKET)
        )
        files = [
            key for key in files
            if key.lower().endswith(".pdf")
        ]

        if s3_key and not files:
            raise ValueError("The requested S3 object is not a PDF file")

        print(f"Found {len(files)} PDF file(s) in S3.")

        for file_number, key in enumerate(files, start=1):
            print(f"\nFile {file_number}: {key}")
            current_document_id = document_id or key

            if self.vector_db.document_exists(current_document_id):
                print("  Status: skipped (already ingested)")
                continue

            print("  Status: downloading")
            pdf_bytes = self.s3.download_file(
                Config.S3_BUCKET,
                key
            )
            print("  Status: downloaded")

            pages = self.pdf_processor.extract_pages(pdf_bytes)
            chunks = self.chunker.create_chunks(pages)
            print(f"  Pages: {len(pages)}")
            print(f"  Chunks: {len(chunks)}")

            for index, chunk in enumerate(chunks, start=1):
                print(f"  Chunk status: {index}/{len(chunks)}")
                embedding = self.embedding_service.create_embedding(
                    chunk["text"]
                )
                self.vector_db.insert_chunk(
                    document_id=current_document_id,
                    chunk_id=chunk["chunk_id"],
                    content=chunk["text"],
                    embedding=embedding,
                    page_number=chunk["page_number"],
                    source=key
                )

            print("  Status: completed")

        self.vector_db.close()
        print("Ingestion completed successfully.")