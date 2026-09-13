import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

    BEDROCK_EMBEDDING_MODEL = os.getenv(
        "BEDROCK_EMBEDDING_MODEL",
        "amazon.titan-embed-text-v2:0"
    )

    BEDROCK_LLM_MODEL = os.getenv("BEDROCK_LLM_MODEL")

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "ragdb")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    TOP_K = int(os.getenv("TOP_K", "5"))
    RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "3"))

    SIMILARITY_THRESHOLD = float(
        os.getenv("SIMILARITY_THRESHOLD", "0.75")
    )

    @classmethod
    def validate(cls):
        required = {
            "DB_HOST": cls.DB_HOST,
            "DB_USER": cls.DB_USER,
            "DB_PASSWORD": cls.DB_PASSWORD,
            "BEDROCK_LLM_MODEL": cls.BEDROCK_LLM_MODEL,
        }

        if required["BEDROCK_LLM_MODEL"] == "<your-bedrock-model-id>":
            required["BEDROCK_LLM_MODEL"] = None

        missing = [
            key for key, value in required.items()
            if not value
        ]
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}"
            ) 