import json
import boto3

from config import Config


class EmbeddingService:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=Config.AWS_REGION
        )

    def create_embedding(self, text):
        body = {
            "inputText": text,
            "dimensions": 1024,
            "normalize": True
        }
        response = self.client.invoke_model(
            modelId=Config.EMBEDDING_MODEL,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )
        response_body = json.loads(
            response["body"].read()
        )
        return response_body["embedding"]