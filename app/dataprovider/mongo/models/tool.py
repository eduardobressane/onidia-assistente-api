from app.dataprovider.mongo.base import db

COLLECTION_NAME = "tool"
collection = db[COLLECTION_NAME]

collection.create_index("nome", unique=True)
