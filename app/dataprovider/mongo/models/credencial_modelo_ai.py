from pymongo import ASCENDING
from app.dataprovider.mongo.base import db

COLLECTION_NAME = "credencial_modelo_ai"
collection = db[COLLECTION_NAME]

# índice composto e único em descricao + id_contratante
collection.create_index(
    [("descricao", ASCENDING), ("id_contratante", ASCENDING)],
    unique=True,
    name="uniq_descricao_id_contratante"
)