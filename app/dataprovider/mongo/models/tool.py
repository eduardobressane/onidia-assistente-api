from app.dataprovider.mongo.base import db
from app.core.exceptions.types import NotFoundError
from bson import ObjectId

COLLECTION_NAME = "tool"
collection = db[COLLECTION_NAME]

collection.create_index("name", unique=True)

def validate_existing_tools(tools: list[dict]):
    for t in tools:
        tool_id = getattr(t.tool, "id", None)
        if not tool_id:
            raise ValueError("Tool precisa ter um id válido")

        exists = collection.find_one({"_id": ObjectId(tool_id)})
        if not exists:
            raise NotFoundError(f"Tool com id {tool_id} não existe")