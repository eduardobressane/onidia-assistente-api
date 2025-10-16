from app.dataprovider.mongo.base import db
from app.core.exceptions.types import NotFoundError

COLLECTION_NAME = "category"
collection = db[COLLECTION_NAME]

collection.create_index("name", unique=True)
