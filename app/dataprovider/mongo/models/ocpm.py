from app.dataprovider.mongo.base import db
from pymongo import ASCENDING
from bson import ObjectId
from app.core.utils.mongo import ensure_object_id
from uuid import UUID

COLLECTION_NAME = "ocp-m"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_name_contractor_id"
)


from bson import ObjectId

def get_ocpm_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},

        # 🔹 Padroniza a lista de service_ids (strings) a partir de tools
        {
            "$addFields": {
                "_service_ids": {
                    "$filter": {
                        "input": {
                            "$map": {
                                "input": {"$ifNull": ["$tools", []]},
                                "as": "t",
                                "in": {"$ifNull": ["$$t.service.id", "$$t.service_id"]}
                            }
                        },
                        "as": "sid",
                        "cond": {"$ne": ["$$sid", None]}
                    }
                }
            }
        },

        # 🔹 Lookup na collection "service" usando ids padronizados
        {
            "$lookup": {
                "from": "service",
                "let": {"service_ids": "$_service_ids"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$in": [
                                    {"$toString": "$_id"},
                                    {"$ifNull": ["$$service_ids", []]}
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "id": {"$toString": "$_id"},
                            "name": 1,
                            "description": 1
                        }
                    }
                ],
                "as": "services_info"
            }
        },

        # 🔹 Monta os tools com o subdocumento service
        {
            "$addFields": {
                "tools": {
                    "$map": {
                        "input": {"$ifNull": ["$tools", []]},
                        "as": "t",
                        "in": {
                            "name": "$$t.name",
                            "description": "$$t.description",
                            "service": {
                                "$let": {
                                    "vars": {
                                        "sid": {"$ifNull": ["$$t.service.id", "$$t.service_id"]}
                                    },
                                    "in": {
                                        "$arrayElemAt": [
                                            {
                                                "$filter": {
                                                    "input": "$services_info",
                                                    "as": "s",
                                                    "cond": {"$eq": ["$$s.id", "$$sid"]}
                                                }
                                            },
                                            0
                                        ]
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },

        # 🔹 Campos finais
        {
            "$project": {
                "_id": 0,
                "_id": {"$toString": "$_id"},
                "name": 1,
                "description": 1,
                "tools": 1
            }
        }
    ]

    cursor = collection.aggregate(pipeline)
    docs = list(cursor)
    return docs[0] if docs else None

def validate_service(db, contractor_id: UUID | None, service_id: str): 
    """
    Valida se o service informado:
      - Existem na base
      - Pertencem ao mesmo contractor_id (se informado)
    """
    service_collection = db["service"]

    oid = ensure_object_id(service_id)

    # Verifica existência e relação com contractor_id
    query = {"_id": oid}
    if contractor_id is not None:
        query["contractor_id"] = str(contractor_id)

    service_data = service_collection.find_one(
        query,
        {"_id": 1, "_id": 1, "contractor_id": 1}
    )

    if not service_data:
        # Segunda verificação: existe, mas pertence a outro contractor?
        exists_any = service_collection.find_one({"_id": oid}, {"contractor_id": 1})
        if exists_any:
            raise BusinessDomainError(
                f"Serviço com id {service_id} não existe."
            )
        raise NotFoundError(f"Serviço com id {service_id} não existe.")
