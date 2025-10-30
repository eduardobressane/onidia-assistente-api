import os
from dotenv import load_dotenv

from typing import List, Optional, Any, Literal
from uuid import UUID
from pydantic import ConfigDict, BaseModel, Field, model_validator, field_validator
from app.core.exceptions.types import NotFoundError, BadRequestError
from bson import ObjectId
import json

URL_BASE_IMG_PUBLIC = os.getenv("URL_BASE_IMG_PUBLIC")

class OCP(BaseModel):
    id: str = Field(...)
    name: str = Field(...)
    type: str = Field(...)

class Tag(BaseModel):
    id: str = Field(...)
    name: str = Field(...)

class Function(BaseModel):
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    action_type: Optional[Literal["GET", "SET"]] = None
    description: Optional[str] = None
    system_message: Optional[str] = None

class Tool(BaseModel):
    id: str
    name: Optional[str] = None
    scope: Optional[dict[str, Any]] = None

class ToolInfo(BaseModel):
    tool: Tool
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    required: bool

class AgentBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2048)
    system_message: str = Field(...)
    enabled: bool = Field(default=True)
    ocps: List[OCP]
    tags: List[Tag]
    functions: Optional[List[Function]] = None

    @model_validator(mode="after")
    def validate_functions_unique(self):
        functions = self.functions or []
        codes = [f.code for f in functions]
        if len(codes) != len(set(codes)):
            raise BadRequestError("Os códigos das funções devem ser únicos dentro do agente.")
        return self

#CREATE/UPDATE

class OCPCreateOrUpdate(BaseModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise NotFoundError(f"OCP com id {v} não existe")
        return v

class TagCreateOrUpdate(BaseModel):
    id: str = Field(...)

class ToolCreateOrUpdate(BaseModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise NotFoundError(f"Tool com id {v} não existe")
        return v

class ToolInfoCreateOrUpdate(BaseModel):
    tool: ToolCreateOrUpdate
    code: str = Field(..., max_length=10)
    name: str = Field(..., max_length=150)
    required: bool = Field(...)

class AgentCreate(AgentBase):
    ocps: List[OCPCreateOrUpdate]
    tags: List[TagCreateOrUpdate]
    tools: Optional[List[ToolInfoCreateOrUpdate]] = None

class AgentUpdate(AgentBase):
    ocps: List[OCPCreateOrUpdate]
    tags: List[TagCreateOrUpdate]
    tools: Optional[List[ToolInfoCreateOrUpdate]] = None

#OUTPUTS
class AgentOutList(BaseModel):
    id: str
    name: str
    description: str
    image: Optional[str]
    enabled: bool

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutList"]:
        if not doc:
            return None

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            image=f"{URL_BASE_IMG_PUBLIC}/agents/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled"),
        )

class AgentOutDetail(AgentBase):
    id: str
    ocps: List[OCP]
    image: Optional[str]
    tools: List[ToolInfo]

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutDetail"]:
        if not doc:
            return None
        
        tags = []
        for c in doc.get("tags", []):
            tags.append({
                "id": str(c.get("id")) if isinstance(c.get("id"), ObjectId) else c.get("id"),
                "name": str(c.get("name"))
            })

        ocps = []
        for o in doc.get("ocps", []):
            ocps.append(
                OCP(
                    id=str(o.get("id")),
                    name=o.get("name"),
                    type=o.get("type")
                ))

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    ToolInfo(
                        tool=Tool(
                            id=str(tool_data.get("id")),
                            name=tool_data.get("name"),
                            scope=tool_data.get("scope"),
                        ),
                        code=t.get("code"),
                        name=t.get("name"),
                        required=t.get("required", False)
                    )
                )

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            image=f"{URL_BASE_IMG_PUBLIC}/agents/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled"),
            tags=tags,
            ocps=ocps,
            functions=doc.get("functions"),
            tools=tools,
        )

class AgentOutInternal(AgentBase):
    id: str
    image: Optional[str]
    contractor_id: Optional[str] = None
    ocps: List[OCP]
    tools: List[ToolInfo]

    model_config = ConfigDict(populate_by_name=True)

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgentOutInternal"]:
        if not doc:
            return None

        tags = []
        for c in doc.get("tags", []):
            tags.append({
                "id": str(c.get("id")) if isinstance(c.get("id"), ObjectId) else c.get("id"),
                "name": str(c.get("name")),
            })

        ocps = []
        for o in doc.get("ocps", []):
            ocps.append(
                OCP(
                    id=str(o.get("id")),
                    name=o.get("name"),
                    type=o.get("type")
                ))

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    ToolInfo(
                        tool=Tool(
                            id=str(tool_data.get("id")),
                            name=tool_data.get("name"),
                            scope=tool_data.get("scope"),
                        ),
                        code=t.get("code"),
                        name=t.get("name"),
                        required=t.get("required", False)
                    )
                )

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            contractor_id=doc.get("contractor_id"),
            image=f"{URL_BASE_IMG_PUBLIC}/agents/{doc.get('_id')}" if doc.get("has_image") else None,
            enabled=doc.get("enabled"),
            tags=tags,
            ocps=ocps,
            functions=doc.get("functions"),
            tools=tools,
        )
