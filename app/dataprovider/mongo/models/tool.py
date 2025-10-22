from app.dataprovider.mongo.base import db
from bson import ObjectId

COLLECTION_NAME = "tool"
collection = db[COLLECTION_NAME]

collection.create_index("name", unique=True)
