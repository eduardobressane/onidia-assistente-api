from app.dataprovider.mongo.base import db
from app.core.exceptions.types import BusinessDomainError, NotFoundError
from bson import ObjectId
from pymongo import ASCENDING
from app.core.utils.mongo import ensure_object_id

COLLECTION_NAME = "assistant"
collection = db[COLLECTION_NAME]

credential_collection = db["credential"]
credential_type_collection = db["credential_type"]
agent_collection = db["agent"]

# index
collection.create_index(
    [("name", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_name_contractor_id"
)

def get_assistant_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},

        # === Enriquecer ai_model da assistente ===
        {
            "$lookup": {
                "from": "credential",
                "let": {"cred_id": "$ai_model.id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$eq": [{"$toString": "$_id"}, "$$cred_id"]}
                        }
                    },
                    {"$project": {"_id": 1, "name": "$description"}}
                ],
                "as": "ai_model_doc"
            }
        },
        {
            "$addFields": {
                "ai_model": {
                    "id": {
                        "$arrayElemAt": [
                            {
                                "$map": {
                                    "input": "$ai_model_doc",
                                    "as": "m",
                                    "in": {"$toString": "$$m._id"}
                                }
                            },
                            0
                        ]
                    },
                    "name": {"$arrayElemAt": ["$ai_model_doc.name", 0]}
                }
            }
        },
        {"$project": {"ai_model_doc": 0}},

        # === Lookup dos agentes ===
        {
            "$lookup": {
                "from": "agent",
                "let": {"agent_ids": "$agents.agent.id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {"$in": [{"$toString": "$_id"}, "$$agent_ids"]}
                        }
                    },
                    {
                        "$project": {
                            "_id": 1,
                            "name": 1,
                            "description": 1,
                            "system_message": 1,
                            "enabled": 1,
                            "contractor_id": 1,
                            "functions": 1
                        }
                    }
                ],
                "as": "agents_docs"
            }
        },

        # === Adicionar detalhes dos agentes ===
        {
            "$addFields": {
                "agents": {
                    "$map": {
                        "input": "$agents",
                        "as": "ag",
                        "in": {
                            "$let": {
                                "vars": {
                                    "doc": {
                                        "$arrayElemAt": [
                                            {
                                                "$filter": {
                                                    "input": "$agents_docs",
                                                    "as": "doc",
                                                    "cond": {
                                                        "$eq": [
                                                            {"$toString": "$$doc._id"},
                                                            "$$ag.agent.id"
                                                        ]
                                                    }
                                                }
                                            },
                                            0
                                        ]
                                    }
                                },
                                "in": {
                                    "$mergeObjects": [
                                        "$$ag",
                                        {
                                            "agent": {
                                                "id": "$$ag.agent.id",
                                                "name": "$$doc.name",
                                                "description": "$$doc.description",
                                                "system_message": "$$doc.system_message",
                                                "enabled": "$$doc.enabled",
                                                "contractor_id": "$$doc.contractor_id"
                                            },
                                            "functions_full": "$$doc.functions"
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        },

        {"$project": {"agents_docs": 0}}
    ]

    docs = collection.aggregate(pipeline).to_list(length=1)
    if not docs:
        return None

    assistant = docs[0]

    # === Enriquecimento em Python ===

    # 1️⃣ Enriquecer ai_model dos agentes (igual ao da assistente)
    model_ids = []

    for ag in assistant["agents"]:
        ai_model = ag.get("ai_model")
        if ai_model and ai_model.get("id"):
            model_ids.append(str(ai_model["id"]))  # converte aqui

    model_ids = list({mid for mid in model_ids if mid})

    if model_ids:
        creds = {
            str(c["_id"]): c.get("description")
            for c in credential_collection.find(
                {"_id": {"$in": [ObjectId(x) for x in model_ids]}}
            )
        }

        for ag in assistant["agents"]:
            ai_model = ag.get("ai_model")
            if ai_model and ai_model.get("id"):
                model_id = str(ai_model["id"])
                ag["ai_model"] = {
                    "id": model_id,
                    "name": creds.get(model_id)
                }

    # 2️⃣ Enriquecer funções (usando agent.functions.code)
    for ag in assistant["agents"]:
        func_map = {f["code"]: f for f in ag.get("functions_full", []) or []}
        for f in ag.get("functions", []):
            code = f["function"]["code"]
            if code in func_map:
                f["function"]["name"] = func_map[code].get("name")
                f["function"]["description"] = func_map[code].get("description")
        ag.pop("functions_full", None)

    # 3️⃣ Enriquecer tools (usando credential_type)
    tool_ids = list(
        {t["tool"]["id"] for ag in assistant["agents"] for t in ag.get("tools", [])}
    )
    if tool_ids:
        tool_docs = {
            str(c["_id"]): c.get("name")
            for c in credential_type_collection.find(
                {"_id": {"$in": [ObjectId(x) for x in tool_ids]}}
            )
        }
        for ag in assistant["agents"]:
            for t in ag.get("tools", []):
                t["tool"]["name"] = tool_docs.get(t["tool"]["id"])

    return assistant


def validate_tools(agent_config: dict, agent_payload: dict):
    """
    Valida as tools do payload de um agente da assistente com base
    nas regras definidas no agente original (configuração do banco)
    e verifica se as tool_ids correspondem a credential_types válidos.
    """
    config_tools = agent_config.get("tools", [])
    payload_tools = agent_payload.get("tools", []) or []

    # --- Verificar duplicidade de nome ---
    names = [t["name"] for t in payload_tools if "name" in t]
    if len(names) != len(set(names)):
        raise BusinessDomainError("Há tools com nomes duplicados no mesmo agente da assistente.")

    # --- Validar regras de max e required ---
    for cfg in config_tools:
        tool_id = cfg["tool"]["id"]
        max_allowed = cfg.get("max", 0)
        required = cfg.get("required", False)

        # 🔍 Verificar se a tool_id é realmente um tipo de credencial válido
        cred_doc = credential_type_collection.find_one({"_id": ObjectId(tool_id)})

        if not cred_doc:
            raise BusinessDomainError(f"A tool '{tool_id}' não foi encontrada.")

        if cred_doc.get("kind") != "tools":
            raise BusinessDomainError(f"O id '{tool_id}' não é uma tool válida.")

        # --- Validar presença e quantidade ---
        matching_tools = [t for t in payload_tools if t["tool"]["id"] == tool_id]
        count = len(matching_tools)

        if required and count == 0:
            raise BusinessDomainError(f"A tool '{tool_id}' é obrigatória, mas não foi incluída.")

        if max_allowed == 1 and count > 1:
            raise BusinessDomainError(f"A tool '{tool_id}' permite apenas uma instância.")
        elif max_allowed > 1 and count > max_allowed:
            raise BusinessDomainError(
                f"A tool '{tool_id}' excede o limite permitido ({max_allowed})."
            )

    # --- Nenhuma tool não prevista no agente original deve ser incluída ---
    allowed_tool_ids = {t["tool"]["id"] for t in config_tools}
    for tool in payload_tools:
        if tool["tool"]["id"] not in allowed_tool_ids:
            raise BusinessDomainError(
                f"A tool '{tool['tool']['id']}' não está permitida neste agente."
            )

def validate_ai_model(credential_id: str):
    """
    Valida se uma credential existe e se é do tipo 'ai_models'.

    Regras:
      - credential_id deve existir na coleção 'credential'
      - O campo credential_type_id deve apontar para um registro existente em 'credential_type'
      - O 'kind' do credential_type deve ser 'ai_models'

    Lança:
      - NotFoundError se credential não existir
      - NotFoundError se credential_type não existir
      - BusinessDomainError se o tipo não for 'ai_models'
    """

    # --- Valida ID ---
    oid = ensure_object_id(credential_id)

    # --- Busca a credential ---
    credential = credential_collection.find_one({"_id": oid})
    if not credential:
        raise NotFoundError(f"Credential com id {credential_id} não existe.")

    credential_type_id = credential.get("credential_type_id")

    # --- Busca o tipo da credential ---
    try:
        type_oid = ObjectId(str(credential_type_id))
    except Exception:
        raise BusinessDomainError("credential_type_id inválido (não é um ObjectId válido).")

    credential_type = credential_type_collection.find_one({"_id": type_oid})
    if not credential_type:
        raise NotFoundError(
            f"Modelo não existe."
        )

    kind = credential_type.get("kind")
    if kind != "ai_models":
        raise BusinessDomainError(
            f"Credential {credential_id} não é um modelo válido."
        )