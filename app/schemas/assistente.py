from typing import List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.core.exceptions.types import NotFoundError
from bson import ObjectId

class Funcao(BaseModel):
    codigo: Optional[str] = None
    nome: Optional[str] = None
    descricao: Optional[str] = None

class Perfil(BaseModel):
    id: str
    nome: Optional[str] = None

class FuncaoAssistente(BaseModel):
    funcao: Optional[Funcao] = None
    system_message_compl: Optional[str] = None
    perfis: Optional[List[Perfil]] = None

class Credencial(BaseModel):
    id: str
    descricao: Optional[str] = None

class ToolInfo(BaseModel):
    id: str
    nome: Optional[str] = None

class Tool(BaseModel):
    tool: ToolInfo
    nome: str

class Agente(BaseModel):
    id: str
    nome: Optional[str] = None
    system_message: Optional[str] = None
    visivel: Optional[bool] = True
    publico: Optional[bool] = True
    ativo: bool = Field(default=True)
    id_contratante: Optional[str] = None

class AgenteAssistente(BaseModel):
    agente: Agente
    nome: Optional[str] = None
    system_message_compl: str = Field(..., title="System Message")
    secreto: Optional[bool] = True
    ativo: Optional[bool] = True
    credencial: Optional[Credencial] = None
    perfis: Optional[List[Perfil]] = None
    funcoes: Optional[List[FuncaoAssistente]] = None
    tools: List[Tool] = []

class AssistenteBase(BaseModel):
    nome: str = Field(..., title="Nome do Agente", max_length=150)
    descricao: str = Field(..., title="Descrição do Agente", max_length=2048)
    ativo: bool = Field(default=True)

#CREATE/UPDATE
class CredencialCreateOrUpdate(BaseModel):
    id: str

class PerfilCreateOrUpdate(BaseModel):
    id: str

class AgenteCreateOrUpdate(BaseModel):
    id: str

class FuncaoCreateOrUpdate(BaseModel):
    codigo: Optional[str] = None

class FuncaoAssistenteCreateOrUpdate(BaseModel):
    funcao: FuncaoCreateOrUpdate
    system_message_compl: str = Field(..., title="System message complementar")
    perfis: Optional[List[PerfilCreateOrUpdate]] = None

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
    nome: str = Field(..., max_length=150)

class AgenteAssistenteCreateOrUpdate(BaseModel):
    agente: AgenteCreateOrUpdate
    nome: str = Field(..., title="Nome do agente na assistente", max_length=150)
    system_message_compl: str = Field(..., title="System message complementar")
    secreto: bool = Field(default=True)
    ativo: bool = Field(default=True)
    credencial: CredencialCreateOrUpdate
    perfis: Optional[List[PerfilCreateOrUpdate]] = None
    funcoes: Optional[List[FuncaoAssistenteCreateOrUpdate]] = None
    tools: Optional[List[ToolCreateOrUpdate]]

class AssistenteCreate(AssistenteBase):
    system_message: str = Field(..., title="System Message")
    credencial: CredencialCreateOrUpdate
    perfis: Optional[List[PerfilCreateOrUpdate]] = None
    agentes: Optional[List[AgenteAssistenteCreateOrUpdate]] = None

class AssistenteUpdate(AssistenteBase):
    credencial: CredencialCreateOrUpdate
    perfis: Optional[List[PerfilCreateOrUpdate]] = None
    agentes: Optional[List[AgenteAssistenteCreateOrUpdate]] = None

#OUTPUTS
class AssistenteOutList(AssistenteBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AssistenteOutList"]:
        if not doc:
            return None

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            descricao=doc.get("descricao"),
            ativo=doc.get("ativo"),
        )

class AssistenteOutDetail(BaseModel):
    id: str
    nome: str
    descricao: str
    system_message: str
    ativo: bool
    credencial: Optional[Credencial]
    perfis: Optional[List[Perfil]] = None
    agentes: Optional[List[AgenteAssistente]] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AssistenteOutDetail"]:
        if not doc:
            return None

        agentes = []
        for a in doc.get("agentes", []):
            if "agente" in a:
                agente_data = a["agente"]
                agentes.append(
                    AgenteAssistente(
                        agente=Agente(
                            id=str(agente_data.get("id")),
                            nome=agente_data.get("nome"),
                            descricao=agente_data.get("descricao"),
                            #system_message=agente_data.get("system_message"),
                            #visivel=agente_data.get("visivel"),
                            ativo=agente_data.get("ativo"),
                            #id_contratante=agente_data.get("id_contratante"),
                        ),
                        nome=a.get("nome"),
                        system_message_compl=a.get("system_message_compl"),
                        secreto=a.get("secreto"),
                        ativo=a.get("ativo"),
                        perfis=a.get("perfis"),
                        funcoes=a.get("funcoes"),
                        tools=a.get("tools"),
                    )
                )

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            descricao=doc.get("descricao"),
            system_message=doc.get("system_message"),
            ativo=doc.get("ativo"),
            credencial=doc.get("credencial"),
            perfis=doc.get("perfis"),
            agentes=agentes
        )

class AssistenteOutInterno(BaseModel):
    id: str
    nome: str
    descricao: str
    system_message: str
    ativo: bool
    credencial: Optional[Credencial]
    perfis: Optional[List[Perfil]] = None
    agentes: Optional[List[AgenteAssistente]] = None

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AssistenteOutInterno"]:
        if not doc:
            return None

        agentes = []
        for a in doc.get("agentes", []):
            if "agente" in a:
                agente_data = a["agente"]

                agentes.append(
                    AgenteAssistente(
                        agente=Agente(
                            id=str(agente_data.get("id")),
                            nome=agente_data.get("nome"),
                            descricao=agente_data.get("descricao"),
                            #system_message=agente_data.get("system_message"),
                            #visivel=agente_data.get("visivel"),
                            ativo=agente_data.get("ativo"),
                            #id_contratante=agente_data.get("id_contratante"),
                        ),
                        nome=a.get("nome"),
                        system_message_compl=a.get("system_message_compl"),
                        secreto=a.get("secreto"),
                        ativo=a.get("ativo"),
                        perfis=a.get("perfis"),
                        funcoes=a.get("funcoes"),
                        tools=a.get("tools"),
                    )
                )

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            descricao=doc.get("descricao"),
            system_message=doc.get("system_message"),
            ativo=doc.get("ativo"),
            credencial=doc.get("credencial"),
            perfis=doc.get("perfis"),
            agentes=agentes
        )