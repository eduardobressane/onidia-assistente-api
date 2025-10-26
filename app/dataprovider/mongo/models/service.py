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
