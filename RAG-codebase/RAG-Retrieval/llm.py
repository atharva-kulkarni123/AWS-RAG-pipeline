import json
from bedrock_client import AWSClient
from config import Config


class LLMService:
    def __init__(self):
        self.client = AWSClient.get_bedrock_runtime()
    def generate(self, prompt: str) -> str:
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "maxTokens": 800,
                "temperature": 0.2
            }
        }

        response = self.client.converse(
            modelId=Config.BEDROCK_LLM_MODEL,
            messages=body["messages"],
            inferenceConfig=body["inferenceConfig"]
        )

        return (
            response["output"]["message"]["content"][0]["text"]
        )