import os
from dotenv import load_dotenv

from fastapi import UploadFile
from io import BytesIO

from app.core.exceptions.types import BadRequestError
from app.services.s3 import S3Service

class UploadService:

    @staticmethod
    def upload_file(id: str, dir: str, file: UploadFile, max_file_size: int, allowed_content_types: dict):
        # 1️⃣ valida tipo MIME
        if file.content_type not in allowed_content_types:
            raise BadRequestError("Tipo de arquivo não permitido. Use apenas JPEG, PNG ou WEBP.")

        # 2️⃣ lê e valida tamanho
        contents = file.file.read()
        size_kb = len(contents) / 1024
        if size_kb > max_file_size:
            raise BadRequestError(
                f"O arquivo é muito grande ({size_kb:.1f} KB). "
                f"Tamanho máximo permitido: {max_file_size} KB."
            )

        # 3️⃣ recria o arquivo (porque .read() move o cursor)
        file.file = BytesIO(contents)
        file.file.seek(0)

        # 4️⃣ faz o upload
        s3 = S3Service()
        public_url = s3.upload_public_file(file, directory="imgs/" + dir, filename=id)

        if not public_url:
            raise BadRequestError("Erro ao salvar a imagem")

        return {"public_url": public_url}

    @staticmethod
    def delete_file(id: str, dir: str):
        s3 = S3Service()
        deleted = s3.delete_public_file("imgs/" + dir, id)

        if not deleted:
            raise BadRequestError("Erro ao excluir a imagem")

        return {"deleted": True}