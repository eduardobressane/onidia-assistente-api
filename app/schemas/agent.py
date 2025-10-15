from typing import List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, field_validator
from app.core.exceptions.types import NotFoundError, BadRequestError
from bson import ObjectId
import json

class Function(BaseModel):
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    description: str = Field(..., max_length=255)
    system_message: str

class Tool(BaseModel):
    id: str
    name: Optional[str] = None
    scope: Optional[dict[str, Any]] = None

class AgentBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2048)
    system_message: str = Field(...)
    public: bool = Field(default=True)
    enabled: bool = Field(default=True)
    functions: Optional[List[Function]] = None
    contractors: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_functions_unique(self):
        functions = self.functions or []
        codes = [f.code for f in functions]
        if len(codes) != len(set(codes)):
            raise BadRequestError("Os códigos das funções devem ser únicos dentro do agente.")
        return self

    @model_validator(mode="after")
    def validate_contractors_unique_and_uuid(self):
        contractors = self.contractors or []
        if not contractors:
            return self  # lista vazia = ok

        standardized = []
        for cid in contractors:
            try:
                # normaliza para UUID válido em lowercase
                standardized.append(str(UUID(str(cid).strip())))
            except ValueError:
                raise BadRequestError(f"Contratante '{cid}' não é um UUID válido.")

        if len(standardized) != len(set(standardized)):
            raise BadRequestError("Os ids dos contratantes devem ser únicos dentro do agente.")

        # sobrescreve padronizado
        self.contractors = standardized
        return self

#CREATE/UPDATE
class ToolCreateOrUpdate(BaseModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise NotFoundError(f"Tool com id {v} não existe")
        return v

class AgentCreate(AgentBase):
    tools: List[ToolCreateOrUpdate]

class AgentUpdate(AgentBase):
    tools: List[ToolCreateOrUpdate]

#OUTPUTS
class AgentOutList(BaseModel):
    id: str
    name: str
    description: str
    public: bool
    visivel: bool
    enabled: bool

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutList"]:
        if not doc:
            return None

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            public=doc.get("public"),
            enabled=doc.get("enabled"),
        )

class AgentOutDetail(AgentBase):
    id: str
    tools: List[Tool]

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutDetail"]:
        if not doc:
            return None

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    Tool(
                        id=str(tool_data.get("id")),
                        name=tool_data.get("name"),
                        scope=tool_data.get("scope"),
                    )
                )

        # Normalizes contractors
        raw_contractors = doc.get("contractors") or []
        contractors: List[str] = []

        if isinstance(raw_contractors, str):
            try:
                raw_contractors = json.loads(raw_contractors)
            except Exception:
                raw_contractors = []

        if isinstance(raw_contractors, list):
            for c in raw_contractors:
                if isinstance(c, list):  # flatten lista de listas
                    for item in c:
                        if item:
                            contractors.append(str(item))
                elif c:
                    contractors.append(str(c))

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            enabled=doc.get("enabled"),
            functions=doc.get("functions"),
            tools=tools,
            contractors=contractors,
        )

class AgentOutInternal(AgentBase):
    id: str
    contractor_id: Optional[str] = None
    tools: List[Tool]

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutInternal"]:
        if not doc:
            return None

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    Tool(
                        id=str(tool_data.get("id")),
                        name=tool_data.get("name"),
                        scope=tool_data.get("scope"),
                    )
                )

        # Normalizes contractors
        raw_contractors = doc.get("contractors") or []
        contractors: List[str] = []

        if isinstance(raw_contractors, str):
            try:
                raw_contractors = json.loads(raw_contractors)
            except Exception:
                raw_contractors = []

        if isinstance(raw_contractors, list):
            for c in raw_contractors:
                if isinstance(c, list):  # flatten lista de listas
                    for item in c:
                        if item:
                            contractors.append(str(item))
                elif c:
                    contractors.append(str(c))

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            contractor_id=doc.get("contractor_id"),
            enabled=doc.get("enabled"),
            functions=doc.get("functions"),
            tools=tools,
            contractors=contractors,
        )
