from app.dataprovider.mongo.base import db
from app.core.exceptions.types import NotFoundError

COLLECTION_NAME = "tool"
collection = db[COLLECTION_NAME]

collection.create_index("nome", unique=True)

async def validar_tools_existentes(tools: list[dict]):
    for t in tools:
        tool_id = t["tool"]["id"]
        exists = await tool_collection.find_one({"_id": ObjectId(tool_id)})
        if not exists:
            raise NotFoundError(f"Tool com id {tool_id} não existe")