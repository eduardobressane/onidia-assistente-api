import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_access_key: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3_bucket: str = os.getenv("S3_BUCKET_NAME", "onidia-model-icons")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")

settings = Settings()
