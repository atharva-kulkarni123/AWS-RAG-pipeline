import json
from bedrock_client import AWSClient
from config import Config


class EmbeddingService:
    def __init__(self):
        self.client = AWSClient.get_bedrock_runtime()
    def generate_embedding(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        request_body = {
            "inputText": text.strip()
        }
        response = self.client.invoke_model(
            modelId=Config.BEDROCK_EMBEDDING_MODEL,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(
            response["body"].read()
        )

        embedding = response_body.get("embedding")

        if not embedding:
            raise RuntimeError(
                "Embedding model returned no embedding"
            )

        return embedding