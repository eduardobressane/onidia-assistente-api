from typing import List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.core.exceptions.types import NotFoundError
from bson import ObjectId

class Function(BaseModel):
    codigo: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class Profile(BaseModel):
    id: str
    name: Optional[str] = None

class FunctionAssistant(BaseModel):
    function: Optional[Function] = None
    system_message_compl: Optional[str] = None
    profiles: Optional[List[Profile]] = None

class Credential(BaseModel):
    id: str
    description: Optional[str] = None

class ToolInfo(BaseModel):
    id: str
    name: Optional[str] = None

class Tool(BaseModel):
    tool: ToolInfo
    name: str

class Agent(BaseModel):
    id: str
    name: Optional[str] = None
    system_message: Optional[str] = None
    visivel: Optional[bool] = True
    publico: Optional[bool] = True
    enabled: bool = Field(default=True)
    contractor_id: Optional[str] = None

class AgentAssistant(BaseModel):
    agent: Agent
    name: Optional[str] = None
    system_message_compl: str = Field(...)
    secret: Optional[bool] = True
    enabled: Optional[bool] = True
    credential: Optional[Credential] = None
    profiles: Optional[List[Profile]] = None
    functions: Optional[List[FunctionAssistant]] = None
    tools: List[Tool] = []

class AssistantBase(BaseModel):
    name: str = Field(..., max_length=150)
    description: str = Field(..., max_length=2048)
    enabled: bool = Field(default=True)

#CREATE/UPDATE
class CredentialCreateOrUpdate(BaseModel):
    id: str

class ProfileCreateOrUpdate(BaseModel):
    id: str

class AgentCreateOrUpdate(BaseModel):
    id: str

class FunctionCreateOrUpdate(BaseModel):
    codigo: str

class FunctionAssistantCreateOrUpdate(BaseModel):
    function: FunctionCreateOrUpdate
    system_message_compl: Optional[str] = None
    profiles: Optional[List[ProfileCreateOrUpdate]] = None

class ToolInfoCreateOrUpdate(BaseModel):
    id: str

    @field_validator("id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not ObjectId.is_valid(v):
            raise NotFoundError(f"Tool com id {v} não existe")
        return v

class ToolCreateOrUpdate(BaseModel):
    tool: ToolInfoCreateOrUpdate
    name: str = Field(..., max_length=150)

class AgentAssistantCreateOrUpdate(BaseModel):
    agent: AgentCreateOrUpdate
    name: str = Field(..., max_length=150)
    system_message_compl: Optional[str] = None
    secret: bool = Field(default=True)
    enabled: bool = Field(default=True)
    credential: CredentialCreateOrUpdate
    profiles: Optional[List[ProfileCreateOrUpdate]] = None
    functions: Optional[List[FunctionAssistantCreateOrUpdate]] = None
    tools: Optional[List[ToolCreateOrUpdate]] = None

class AssistantCreate(AssistantBase):
    system_message: str = Field(..., title="System Message")
    credential: CredentialCreateOrUpdate
    profiles: Optional[List[ProfileCreateOrUpdate]] = None
    agents: Optional[List[AgentAssistantCreateOrUpdate]] = None

class AssistantUpdate(AssistantBase):
    credential: CredentialCreateOrUpdate
    profiles: Optional[List[ProfileCreateOrUpdate]] = None
    agents: Optional[List[AgentAssistantCreateOrUpdate]] = None

#OUTPUTS
class AssistantOutList(AssistantBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AssistantOutList"]:
        if not doc:
            return None

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            enabled=doc.get("enabled"),
        )

class AssistantOutDetail(BaseModel):
    id: str
    name: str
    description: str
    system_message: str
    enabled: bool
    credential: Optional[Credential]
    profiles: Optional[List[Profile]] = None
    agents: Optional[List[AgentAssistant]] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AssistantOutDetail"]:
        if not doc:
            return None

        agents = []
        for a in doc.get("agents", []):
            if "agent" in a:
                agent_data = a["agent"]
                agents.append(
                    AgentAssistant(
                        agent=Agent(
                            id=str(agent_data.get("id")),
                            name=agent_data.get("name"),
                            description=agent_data.get("description"),
                            #system_message=agent_data.get("system_message"),
                            #visivel=agent_data.get("visivel"),
                            enabled=agent_data.get("enabled"),
                            #contractor_id=agent_data.get("contractor_id"),
                        ),
                        name=a.get("name"),
                        system_message_compl=a.get("system_message_compl"),
                        secret=a.get("secret"),
                        enabled=a.get("enabled"),
                        profiles=a.get("profiles"),
                        functions=a.get("functions"),
                        tools=a.get("tools"),
                    )
                )

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            enabled=doc.get("enabled"),
            credential=doc.get("credential"),
            profiles=doc.get("profiles"),
            agents=agents
        )

class AssistantOutInternal(BaseModel):
    id: str
    name: str
    description: str
    system_message: str
    enabled: bool
    credential: Optional[Credential]
    profiles: Optional[List[Profile]] = None
    agents: Optional[List[AgentAssistant]] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AssistantOutInternal"]:
        if not doc:
            return None

        agents = []
        for a in doc.get("agents", []):
            if "agent" in a:
                agent_data = a["agent"]

                agents.append(
                    AgentAssistant(
                        agent=Agent(
                            id=str(agent_data.get("id")),
                            name=agent_data.get("name"),
                            description=agent_data.get("description"),
                            #system_message=agent_data.get("system_message"),
                            #visivel=agent_data.get("visivel"),
                            enabled=agent_data.get("enabled"),
                            #contractor_id=agent_data.get("contractor_id"),
                        ),
                        name=a.get("name"),
                        system_message_compl=a.get("system_message_compl"),
                        secret=a.get("secret"),
                        enabled=a.get("enabled"),
                        profiles=a.get("profiles"),
                        functions=a.get("functions"),
                        tools=a.get("tools"),
                    )
                )

        return cls(
            id=str(doc["_id"]),
            name=doc.get("name"),
            description=doc.get("description"),
            system_message=doc.get("system_message"),
            enabled=doc.get("enabled"),
            credential=doc.get("credential"),
            profiles=doc.get("profiles"),
            agents=agents
        )