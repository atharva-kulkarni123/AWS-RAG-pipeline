import boto3
from config import Config

class AWSClient:

    @staticmethod
    def get_bedrock_runtime():
        return boto3.client(
            "bedrock-runtime",
            region_name=Config.AWS_REGION
        )