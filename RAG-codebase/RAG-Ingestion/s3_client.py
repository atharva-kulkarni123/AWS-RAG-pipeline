import boto3
from config import Config


class S3Client:

    def __init__(self):
        self.client = boto3.client("s3", region_name=Config.AWS_REGION)

    def list_files(self, bucket, prefix=""):
        paginator = self.client.get_paginator("list_objects_v2")
        files = []

        for page in paginator.paginate(
            Bucket=bucket,
            Prefix=prefix
        ):
            files.extend(
                item["Key"]
                for item in page.get("Contents", [])
                if not item["Key"].endswith("/")
            )

        return files

    def download_file(self, bucket, key):

        response = self.client.get_object(
            Bucket=bucket,
            Key=key
        )

        return response["Body"].read()