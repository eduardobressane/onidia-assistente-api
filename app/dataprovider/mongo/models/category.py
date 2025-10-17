from app.dataprovider.mongo.base import db
from pymongo import ASCENDING

COLLECTION_NAME = "category"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("category_type", ASCENDING)],
    unique=True,
    name="uniq_name_category_type"
)
