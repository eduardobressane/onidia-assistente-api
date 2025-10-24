from app.dataprovider.mongo.base import db
from pymongo import ASCENDING
from bson import ObjectId
from app.core.exceptions.types import NotFoundError

COLLECTION_NAME = "tag"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("tag_type", ASCENDING)],
    unique=True,
    name="uniq_name_tag_type"
)

def validate_existing_tags(tags: list[dict], tag_type: str):
    for c in tags:
        tag_id = c["id"] if isinstance(c, dict) else c.id
        exists = collection.find_one({
            "_id": ObjectId(tag_id),
            "tag_type": tag_type
        })

        if not exists:
            raise NotFoundError(f"Tag com id {tag_id} não existe")