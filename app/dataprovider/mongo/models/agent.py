from app.dataprovider.mongo.base import db
from app.core.exceptions.types import BusinessDomainError, NotFoundError
from bson import ObjectId
from pymongo import ASCENDING
from uuid import UUID

COLLECTION_NAME = "agent"
collection = db[COLLECTION_NAME]

tool_collection = db["tool"]
ocp_collection = db["ocp"]

# index
collection.create_index(
    [("name", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_name_contractor_id"
)

def get_agent_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},
        {"$unwind": {"path": "$ocps", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "ocp",
            "localField": "ocps._id",
            "foreignField": "id",
            "as": "ocp_info"
        }},
        {"$unwind": {"path": "$ocp_info", "preserveNullAndEmptyArrays": True}},

        {"$unwind": {"path": "$tools", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "tool",
            "localField": "tools._id",
            "foreignField": "id",
            "as": "tool_info"
        }},
        {"$unwind": {"path": "$tool_info", "preserveNullAndEmptyArrays": True}},

        {"$unwind": {"path": "$categories", "preserveNullAndEmptyArrays": True}},
        {"$lookup": {
            "from": "category",
            "localField": "categories._id",
            "foreignField": "id",
            "as": "category_info"
        }},
        {"$unwind": {"path": "$category_info", "preserveNullAndEmptyArrays": True}},

        {"$addFields": {
            "ocps": {
                "id": "$ocp_info._id",
                "name": {"$ifNull": ["$ocp_info.name", ""]},
                "type": {"$ifNull": ["$ocp_info.ocp.metadata.source.type", ""]}
            },
            "tools": {
                "tool": {
                    "id": "$tool_info._id",
                    "name": "$tool_info.name",
                    "scope": "$tool_info.scope"
                },
                "max": {"$ifNull": ["$tools.max", 1]},
                "required": {"$ifNull": ["$tools.required", False]}
            },
            "categories": {
                "id": "$category_info._id",
                "name": "$category_info.name"
            }
        }},
        {"$group": {
            "_id": "$_id",
            "name": {"$first": "$name"},
            "description": {"$first": "$description"},
            "system_message": {"$first": "$system_message"},
            "is_public": {"$first": "$is_public"},
            "enabled": {"$first": "$enabled"},
            "contractor_id": {"$first": "$contractor_id"},
            "categories": {"$push": "$categories"},
            "ocps": {"$push": "$ocps"},
            "functions": {"$first": "$functions"},
            "tools": {"$push": "$tools"},
            "contractors": {"$first": "$contractors"}
        }}
    ]

    cursor = collection.aggregate(pipeline)
    docs = cursor.to_list(length=1)
    return docs[0] if docs else None

def _extract_id(candidate, key_chain=("id", "_id")) -> str | None:
    """Extrai o id de um dict ou objeto (tentando 'id' e '_id')."""
    if candidate is None:
        return None

    for key in key_chain:
        if isinstance(candidate, dict) and key in candidate:
            return str(candidate[key])
        if hasattr(candidate, key):
            val = getattr(candidate, key)
            if val:
                return str(val)

    return None


def _to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(str(id_str))
    except Exception:
        raise BusinessDomainError("Id inválido (não é um ObjectId válido).")


def validate_tools(db, tools: list[dict]):
    """
    Espera itens como:
      {"tool": {"id": "...", ...}, "max": 1, "required": True}
    ou um objeto Pydantic com atributo .tool.id

    Exemplo de uso:
      validate_tools(agent.tools, db)
    """
    tool_collection = db["tool"]

    for t in tools or []:
        tool_obj = getattr(t, "tool", None) or (t.get("tool") if isinstance(t, dict) else None) or t
        tool_id = _extract_id(tool_obj)
        if not tool_id:
            raise BusinessDomainError("Tool precisa ter um id válido.")

        oid = _to_object_id(tool_id)
        exists = tool_collection.find_one({"_id": oid}, {"_id": 1})
        if not exists:
            raise NotFoundError(f"Tool com id {tool_id} não existe.")


from uuid import UUID
from app.core.exceptions.types import BusinessDomainError, NotFoundError
from bson import ObjectId


def validate_ocps(db, contractor_id: UUID | None, ocps: list[dict]):
    """
    Valida se os OCPs informados:
      - Existem na base
      - Pertencem ao mesmo contractor_id (se informado)
      - Não estão repetidos
      - Se houver tipo 'langserve', deve haver apenas 1 OCP

    Espera itens como:
        {"id": "...", ...}
    ou objeto Pydantic com atributo .id

    Exemplo:
        validate_ocps(db, agent.contractor_id, agent.ocps)
    """
    ocp_collection = db["ocp"]
    ocp_types = []     # armazenará os tipos encontrados
    ocp_ids_seen = set()  # para detectar duplicados

    for o in ocps or []:
        ocp_id = _extract_id(o)
        if not ocp_id:
            raise BusinessDomainError("OCP precisa ter um id válido.")

        # Verifica duplicidade
        if ocp_id in ocp_ids_seen:
            raise BusinessDomainError(f"OCP duplicado detectado: {ocp_id}")
        ocp_ids_seen.add(ocp_id)

        oid = _to_object_id(ocp_id)

        # Verifica existência e relação com contractor_id
        query = {"_id": oid}
        if contractor_id is not None:
            query["contractor_id"] = str(contractor_id)

        ocp_data = ocp_collection.find_one(
            query,
            {"_id": 1, "ocp.metadata.source.type": 1, "contractor_id": 1}
        )

        if not ocp_data:
            # Segunda verificação: existe, mas pertence a outro contractor?
            exists_any = ocp_collection.find_one({"_id": oid}, {"contractor_id": 1})
            if exists_any:
                raise BusinessDomainError(
                    f"OCP com id {ocp_id} não existe."
                )
            raise NotFoundError(f"OCP com id {ocp_id} não existe.")

        # Extrai tipo do documento encontrado
        ocp_type = (
            ocp_data.get("ocp", {})
            .get("metadata", {})
            .get("source", {})
            .get("type")
        )
        if ocp_type:
            ocp_types.append(ocp_type)

    # --- Regras de negócio sobre tipos ---
    langserve_count = sum(1 for t in ocp_types if t == "langserve")
    if langserve_count > 0 and len(ocps) > 1:
        raise BusinessDomainError(
            "Quando há um OCP do tipo 'langserve', apenas um OCP é permitido."
        )