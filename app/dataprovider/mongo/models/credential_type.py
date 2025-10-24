from app.dataprovider.mongo.base import db

COLLECTION_NAME = "credential_type"
collection = db[COLLECTION_NAME]

collection.create_index("name", unique=True)
