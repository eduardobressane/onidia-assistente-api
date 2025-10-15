from app.dataprovider.mongo.base import db
from bson import ObjectId
from pymongo import ASCENDING

COLLECTION_NAME = "assistente"
collection = db[COLLECTION_NAME]

# índice composto e único em nome + id_contratante
collection.create_index(
    [("nome", ASCENDING), ("id_contratante", ASCENDING)],
    unique=True,
    name="uniq_nome_id_contratante"
)


def get_assistente_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},

        # --- Lookup dos agentes ---
        {"$lookup": {
            "from": "agente",
            "let": {"agentes_ids": "$agentes.agente.id"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {"$in": [{"$toString": "$_id"}, "$$agentes_ids"]}
                    }
                },
                # traz também funcoes para enriquecer por codigo
                {"$project": {"_id": 1, "nome": 1, "descricao": 1, "ativo": 1, "funcoes": 1}}
            ],
            "as": "agentes_docs"
        }},

        # --- Monta agentes.agente e ENRIQUECE agentes.funcoes.funcao com nome/descricao ---
        {"$addFields": {
            "agentes": {
                "$map": {
                    "input": "$agentes",
                    "as": "ag",
                    "in": {
                        "$let": {
                            "vars": {
                                "doc": {
                                    "$arrayElemAt": [
                                        {
                                            "$filter": {
                                                "input": "$agentes_docs",
                                                "as": "doc",
                                                "cond": {
                                                    "$eq": [
                                                        {"$toString": "$$doc._id"},
                                                        "$$ag.agente.id"
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
                                        "agente": {
                                            "id": "$$ag.agente.id",
                                            "nome": "$$doc.nome",
                                            "descricao": "$$doc.descricao",
                                            "ativo": "$$doc.ativo"
                                        }
                                    },
                                    # ENRIQUECE funções externas do agente
                                    {
                                        "funcoes": {
                                            "$map": {
                                                "input": {"$ifNull": ["$$ag.funcoes", []]},
                                                "as": "f",
                                                "in": {
                                                    "$let": {
                                                        "vars": {
                                                            "f_doc": {
                                                                "$arrayElemAt": [
                                                                    {
                                                                        "$filter": {
                                                                            "input": {"$ifNull": ["$$doc.funcoes", []]},
                                                                            "as": "fd",
                                                                            "cond": {
                                                                                "$eq": ["$$fd.codigo", "$$f.funcao.codigo"]
                                                                            }
                                                                        }
                                                                    },
                                                                    0
                                                                ]
                                                            }
                                                        },
                                                        "in": {
                                                            "$mergeObjects": [
                                                                "$$f",
                                                                {
                                                                    "funcao": {
                                                                        "$mergeObjects": [
                                                                            "$$f.funcao",
                                                                            {
                                                                                "nome": {
                                                                                    "$ifNull": ["$$f_doc.nome", "$$f.funcao.nome"]
                                                                                },
                                                                                "descricao": {
                                                                                    "$ifNull": ["$$f_doc.descricao", "$$f.funcao.descricao"]
                                                                                }
                                                                            }
                                                                        ]
                                                                    }
                                                                }
                                                            ]
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }},

        {"$project": {"agentes_docs": 0}},

        # --- Lookup dos tools ---
        {"$lookup": {
            "from": "tool",
            "let": {"tools_ids": {
                "$reduce": {
                    "input": {
                        "$map": {
                            "input": "$agentes",
                            "as": "ag",
                            "in": {
                                "$map": {
                                    "input": {"$ifNull": ["$$ag.tools", []]},
                                    "as": "t",
                                    "in": "$$t.tool.id"
                                }
                            }
                        }
                    },
                    "initialValue": [],
                    "in": {"$setUnion": ["$$value", "$$this"]}
                }
            }},
            "pipeline": [
                {"$match": {"$expr": {"$in": [{"$toString": "$_id"}, "$$tools_ids"]}}},
                {"$project": {"_id": 1, "nome": 1, "ativo": 1}}
            ],
            "as": "tools_docs"
        }},

        # --- Enriquecer tools de cada agente ---
        {"$addFields": {
            "agentes": {
                "$map": {
                    "input": "$agentes",
                    "as": "ag",
                    "in": {
                        "$mergeObjects": [
                            "$$ag",
                            {
                                "tools": {
                                    "$map": {
                                        "input": {"$ifNull": ["$$ag.tools", []]},
                                        "as": "t",
                                        "in": {
                                            "$let": {
                                                "vars": {
                                                    "t_doc": {
                                                        "$arrayElemAt": [
                                                            {
                                                                "$filter": {
                                                                    "input": "$tools_docs",
                                                                    "as": "td",
                                                                    "cond": {
                                                                        "$eq": [
                                                                            {"$toString": "$$td._id"},
                                                                            "$$t.tool.id"
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
                                                        "$$t",
                                                        {
                                                            "tool": {
                                                                "id": "$$t.tool.id",
                                                                "nome": "$$t_doc.nome",
                                                                "ativo": "$$t_doc.ativo"
                                                            }
                                                        }
                                                    ]
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }},

        {"$project": {"tools_docs": 0}}
    ]

    cursor = collection.aggregate(pipeline)
    docs = cursor.to_list(length=1)
    return docs[0] if docs else None
