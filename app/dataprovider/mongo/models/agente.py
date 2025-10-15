from app.dataprovider.mongo.base import db
from bson import ObjectId
from pymongo import ASCENDING

COLLECTION_NAME = "agente"
collection = db[COLLECTION_NAME]

# índice composto e único em nome + id_contratante
collection.create_index(
    [("nome", ASCENDING), ("id_contratante", ASCENDING)],
    unique=True,
    name="uniq_nome_id_contratante"
)

def get_agente_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},
        {"$unwind": {"path": "$tools", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "tool",
            "localField": "tools._id",
            "foreignField": "id",
            "as": "tool_info"
        }},
        {"$unwind": {"path": "$tool_info", "preserveNullAndEmptyArrays": True}},
        {"$addFields": {
            "tools.tool": {
                "id": "$tool_info._id",
                "nome": "$tool_info.nome",
                "escopo": "$tool_info.escopo"
            }
        }},
        {"$group": {
            "_id": "$_id",
            "nome": {"$first": "$nome"},
            "descricao": {"$first": "$descricao"},
            "system_message": {"$first": "$system_message"},
            "visivel": {"$first": "$visivel"},
            "publico": {"$first": "$publico"},
            "ativo": {"$first": "$ativo"},
            "id_contratante": {"$first": "$id_contratante"},
            "funcoes": {"$first": "$funcoes"},
            "tools": {"$push": "$tools"},
            "contratantes": {"$first": "$contratantes"}
        }}
    ]

    cursor = collection.aggregate(pipeline)
    docs = cursor.to_list(length=1)
    return docs[0] if docs else None

