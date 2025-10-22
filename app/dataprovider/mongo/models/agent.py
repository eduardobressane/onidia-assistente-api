from app.dataprovider.mongo.base import db
from app.core.exceptions.types import BusinessDomainError, NotFoundError
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

        {"$unwind": {"path": "$categories", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "category",
            "localField": "categories._id",
            "foreignField": "id",
            "as": "category_info"
        }},
        {"$unwind": {"path": "$category_info", "preserveNullAndEmptyArrays": True}},

        {"$addFields": {
            "tools": {
                "tool": {
                    "id": "$tool_info._id",
                    "name": "$tool_info.name",
                    "scope": "$tool_info.scope"
                },
                "max": {"$ifNull": ["$tools.max", 1]},
                "required": {"$ifNull": ["$tools.required", False]}
            },
            "categories": {
                "id": "$category_info._id",
                "name": "$category_info.name"
            }
        }},
        {"$group": {
            "_id": "$_id",
            "name": {"$first": "$name"},
            "description": {"$first": "$description"},
            "system_message": {"$first": "$system_message"},
            "is_public": {"$first": "$is_public"},
            "enabled": {"$first": "$enabled"},
            "contractor_id": {"$first": "$contractor_id"},
            "categories": {"$push": "$categories"},
            "functions": {"$first": "$functions"},
            "tools": {"$push": "$tools"},
            "contractors": {"$first": "$contractors"}
        }}
    ]

    cursor = collection.aggregate(pipeline)
    docs = cursor.to_list(length=1)
    return docs[0] if docs else None

def validate_tools(tools: list[dict]):
    for t in tools:
        tool_id = getattr(t.tool, "id", None)
        if not tool_id:
            raise BusinessDomainError("Tool precisa ter um id válido")

        exists = collection.find_one({"_id": ObjectId(tool_id)})
        if not exists:
            raise NotFoundError(f"Tool com id {tool_id} não existe")