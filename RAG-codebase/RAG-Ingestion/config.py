import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    AWS_REGION = os.getenv("AWS_REGION")

    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_KEY = os.getenv("S3_KEY")

    EMBEDDING_MODEL = os.getenv(
        "BEDROCK_EMBEDDING_MODEL"
    )

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")