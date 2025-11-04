from app.dataprovider.mongo.base import db
from pymongo import ASCENDING
from bson import ObjectId

COLLECTION_NAME = "service"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_name_contractor_id"
)

def get_service_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},

        # 🔹 Lookup Authenticator
        {
            "$lookup": {
                "from": "authenticator",
                "let": {"auth_id": "$authenticator.id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$eq": [
                                    {"$toString": "$_id"},
                                    {"$ifNull": ["$$auth_id", None]}
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "id": {"$toString": "$_id"},
                            "name": 1
                        }
                    }
                ],
                "as": "authenticator_info"
            }
        },

        # 🔹 Se encontrar, usa. Senão, mantém id e nome nulo
        {
            "$addFields": {
                "authenticator": {
                    "$cond": [
                        { "$gt": [ { "$size": "$authenticator_info" }, 0 ] },
                        { "$arrayElemAt": ["$authenticator_info", 0] },
                        {
                            "id": "$authenticator.id",
                            "name": None
                        }
                    ]
                }
            }
        },

        # 🔹 Campos finais
        {
            "$project": {
                "_id": {"$toString": "$_id"},
                "name": 1,
                "description": 1,
                "url": 1,
                "method": 1,
                "enabled": 1,
                "headers": 1,
                "authenticator": 1,
                "input_schema": 1,
                "contractor_id": 1
            }
        }
    ]

    docs = list(collection.aggregate(pipeline))
    return docs[0] if docs else None