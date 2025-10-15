from app.dataprovider.mongo.base import db
from bson import ObjectId
from pymongo import ASCENDING

COLLECTION_NAME = "agent"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_name_contractor_id"
)

def get_agent_detail(id: str):
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
                "nome": "$tool_info.name",
                "escopo": "$tool_info.scope"
            }
        }},
        {"$group": {
            "_id": "$_id",
            "name": {"$first": "$name"},
            "description": {"$first": "$description"},
            "system_message": {"$first": "$system_message"},
            "public": {"$first": "$public"},
            "enabled": {"$first": "$enabled"},
            "contractor_id": {"$first": "$contractor_id"},
            "functions": {"$first": "$functions"},
            "tools": {"$push": "$tools"},
            "contractors": {"$first": "$contractors"}
        }}
    ]

    cursor = collection.aggregate(pipeline)
    docs = cursor.to_list(length=1)
    return docs[0] if docs else None

