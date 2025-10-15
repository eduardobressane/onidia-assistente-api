from pymongo import ASCENDING
from app.dataprovider.mongo.base import db

COLLECTION_NAME = "ai_model_credentials"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("description", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_description_contractor_id"
)