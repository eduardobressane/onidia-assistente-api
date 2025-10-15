from app.dataprovider.mongo.base import db
from bson import ObjectId
from pymongo import ASCENDING

COLLECTION_NAME = "assistant"
collection = db[COLLECTION_NAME]

# index
collection.create_index(
    [("name", ASCENDING), ("contractor_id", ASCENDING)],
    unique=True,
    name="uniq_name_contractor_id"
)


def get_assistant_detail(id: str):
    pipeline = [
        {"$match": {"_id": ObjectId(id)}},

        # --- Lookup dos agentes ---
        {"$lookup": {
            "from": "agent",
            "let": {"agents_ids": "$agents.agent.id"},
            "pipeline": [
                {
                    "$match": {
                        "$expr": {"$in": [{"$toString": "$_id"}, "$$agents_ids"]}
                    }
                },
                # traz também funcoes para enriquecer por codigo
                {"$project": {"_id": 1, "name": 1, "description": 1, "enabled": 1, "functions": 1}}
            ],
            "as": "agents_docs"
        }},

        # --- Monta agentes.agente e ENRIQUECE agentes.funcoes.funcao com nome/descricao ---
        {"$addFields": {
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
                                            "enabled": "$$doc.enabled"
                                        }
                                    },
                                    # ENRIQUECE funções externas do agente
                                    {
                                        "functions": {
                                            "$map": {
                                                "input": {"$ifNull": ["$$ag.functions", []]},
                                                "as": "f",
                                                "in": {
                                                    "$let": {
                                                        "vars": {
                                                            "f_doc": {
                                                                "$arrayElemAt": [
                                                                    {
                                                                        "$filter": {
                                                                            "input": {"$ifNull": ["$$doc.functions", []]},
                                                                            "as": "fd",
                                                                            "cond": {
                                                                                "$eq": ["$$fd.code", "$$f.funcao.code"]
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
                                                                    "function": {
                                                                        "$mergeObjects": [
                                                                            "$$f.function",
                                                                            {
                                                                                "name": {
                                                                                    "$ifNull": ["$$f_doc.name", "$$f.function.name"]
                                                                                },
                                                                                "description": {
                                                                                    "$ifNull": ["$$f_doc.description", "$$f.function.description"]
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

        {"$project": {"agents_docs": 0}},

        # --- Lookup dos tools ---
        {"$lookup": {
            "from": "tool",
            "let": {"tools_ids": {
                "$reduce": {
                    "input": {
                        "$map": {
                            "input": "$agents",
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
                {"$project": {"_id": 1, "name": 1, "enabled": 1}}
            ],
            "as": "tools_docs"
        }},

        # --- Enriquecer tools de cada agente ---
        {"$addFields": {
            "agents": {
                "$map": {
                    "input": "$agents",
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
                                                                "name": "$$t_doc.name",
                                                                "enabled": "$$t_doc.enabled"
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
