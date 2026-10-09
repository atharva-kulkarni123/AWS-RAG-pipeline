from ingestion.ingestion import IngestionService


def run_ingestion(s3_key=None, document_id=None):
    """Ingest one S3 object or all configured S3 documents."""
    ingestion = IngestionService()
    ingestion.ingest(s3_key=s3_key, document_id=document_id)


if __name__ == "__main__":
    run_ingestion()