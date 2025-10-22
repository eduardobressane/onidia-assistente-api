import boto3
from botocore.exceptions import ClientError
from typing import Optional
from app.core.s3 import settings
from fastapi import UploadFile
import os


class S3Service:
    def __init__(self):
        self.bucket_name = settings.s3_bucket
        self.region = settings.s3_region
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key,
            aws_secret_access_key=settings.aws_secret_key,
            region_name=settings.s3_region
        )

    def upload_public_file(
        self,
        file: UploadFile,
        directory: str = "ai_models",
        filename: Optional[str] = None
    ) -> Optional[str]:
        """
        Faz upload de um arquivo recebido do FastAPI diretamente para o S3,
        salvando SEM extensão no nome.
        Retorna a URL pública.
        """
        try:
            # ✅ Força nome SEM extensão
            if filename:
                # mesmo que você passe "68f4df0b9511c879c164a68b.png", corta a extensão
                final_name, _ = os.path.splitext(filename)
            else:
                # remove extensão do arquivo original
                final_name, _ = os.path.splitext(file.filename)

            key = f"public/{directory.strip('/')}/{final_name}"

            # Garante que o ponteiro do arquivo esteja no início
            file.file.seek(0)

            # Faz o upload (sem extensão na key)
            self.client.upload_fileobj(
                Fileobj=file.file,
                Bucket=self.bucket_name,
                Key=key,  # 👈 agora sem .png
                ExtraArgs={"ContentType": file.content_type},
            )

            public_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            return public_url

        except ClientError as e:
            print(f"[S3Service] Error uploading file: {e}")
            return None

    def delete_public_file(
        self,
        directory: str,
        filename: str,
    ) -> bool:
        """
        Deleta um arquivo público do bucket S3.
        Retorna True se deletado com sucesso, False caso contrário.
        """
        key = f"public/{directory.strip('/')}/{filename}"

        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            return True

        except ClientError as e:
            print(f"[S3Service] Error deleting file: {e}")
            return False
