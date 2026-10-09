import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
workspace_env = BASE_DIR / ".env"
ingestion_env = Path(__file__).resolve().parent / ".env"

load_dotenv(workspace_env, override=False)
load_dotenv(ingestion_env, override=True)


class Config:

    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_KEY = os.getenv("S3_KEY")

    BEDROCK_EMBEDDING_MODEL = os.getenv(
        "BEDROCK_EMBEDDING_MODEL",
        "amazon.titan-embed-text-v2:0"
    )
    EMBEDDING_MODEL = BEDROCK_EMBEDDING_MODEL

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")