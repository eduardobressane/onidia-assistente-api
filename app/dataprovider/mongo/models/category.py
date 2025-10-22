from app.dataprovider.mongo.base import db
from pymongo import ASCENDING
from bson import ObjectId
from app.core.exceptions.types import NotFoundError

COLLECTION_NAME = "category"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("category_type", ASCENDING)],
    unique=True,
    name="uniq_name_category_type"
)

def validate_existing_categories(categories: list[dict], category_type: str):
    for c in categories:
        category_id = c["id"] if isinstance(c, dict) else c.id
        exists = collection.find_one({
            "_id": ObjectId(category_id),
            "category_type": category_type
        })

        if not exists:
            raise NotFoundError(f"Categoria com id {category_id} não existe")