from app.dataprovider.mongo.base import db

COLLECTION_NAME = "ai_model"
collection = db[COLLECTION_NAME]

collection.create_index("name", unique=True)
