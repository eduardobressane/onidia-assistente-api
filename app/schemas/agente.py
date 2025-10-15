from typing import List, Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, field_validator
from app.core.exceptions.types import NotFoundError, BadRequestError
from bson import ObjectId
import json


class Funcao(BaseModel):
    codigo: str = Field(..., max_length=10)
    nome: str = Field(..., max_length=150)
    descricao: str = Field(..., max_length=255)
    system_message: str

class Tool(BaseModel):
    id: str
    nome: Optional[str] = None
    escopo: Optional[dict[str, Any]] = None

class AgenteBase(BaseModel):
    nome: str = Field(..., title="Nome do Agente", max_length=150)
    descricao: str = Field(..., title="Descrição do Agente", max_length=2048)
    system_message: str = Field(..., title="System Message")
    visivel: bool = Field(default=True)
    publico: bool = Field(default=True)
    ativo: bool = Field(default=True)
    funcoes: Optional[List[Funcao]] = None
    contratantes: Optional[List[str]] = None

    @model_validator(mode="after")
    def validate_funcoes_unique(self):
        funcoes = self.funcoes or []
        codigos = [f.codigo for f in funcoes]
        if len(codigos) != len(set(codigos)):
            raise BadRequestError("Os códigos das funções devem ser únicos dentro do agente.")
        return self

    @model_validator(mode="after")
    def validate_contratantes_unique_and_uuid(self):
        contratantes = self.contratantes or []
        if not contratantes:
            return self  # lista vazia = ok

        normalizados = []
        for cid in contratantes:
            try:
                # normaliza para UUID válido em lowercase
                normalizados.append(str(UUID(str(cid).strip())))
            except ValueError:
                raise BadRequestError(f"Contratante '{cid}' não é um UUID válido.")

        if len(normalizados) != len(set(normalizados)):
            raise BadRequestError("Os ids dos contratantes devem ser únicos dentro do agente.")

        # sobrescreve padronizado
        self.contratantes = normalizados
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

class AgenteCreate(AgenteBase):
    tools: List[ToolCreateOrUpdate]

class AgenteUpdate(AgenteBase):
    tools: List[ToolCreateOrUpdate]

#OUTPUTS
class AgenteOutList(BaseModel):
    id: str
    nome: str
    descricao: str
    publico: bool
    visivel: bool
    ativo: bool

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgenteOutList"]:
        if not doc:
            return None

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            descricao=doc.get("descricao"),
            publico=doc.get("publico"),
            visivel=doc.get("visivel"),
            ativo=doc.get("ativo"),
        )

class AgenteOutDetail(AgenteBase):
    id: str
    tools: List[Tool]

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgenteOutDetail"]:
        if not doc:
            return None

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    Tool(
                        id=str(tool_data.get("id")),
                        nome=tool_data.get("nome"),
                        escopo=tool_data.get("escopo"),
                    )
                )

        # Normaliza contratantes
        raw_contratantes = doc.get("contratantes") or []
        contratantes: List[str] = []

        if isinstance(raw_contratantes, str):
            try:
                raw_contratantes = json.loads(raw_contratantes)
            except Exception:
                raw_contratantes = []

        if isinstance(raw_contratantes, list):
            for c in raw_contratantes:
                if isinstance(c, list):  # flatten lista de listas
                    for item in c:
                        if item:
                            contratantes.append(str(item))
                elif c:
                    contratantes.append(str(c))

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            descricao=doc.get("descricao"),
            system_message=doc.get("system_message"),
            visivel=doc.get("visivel"),
            ativo=doc.get("ativo"),
            funcoes=doc.get("funcoes"),
            tools=tools,
            contratantes=contratantes,
        )

class AgenteOutInterno(AgenteBase):
    id: str
    id_contratante: Optional[str] = None
    tools: List[Tool]

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AgenteOutInterno"]:
        if not doc:
            return None

        tools = []
        for t in doc.get("tools", []):
            if "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    Tool(
                        id=str(tool_data.get("id")),
                        nome=tool_data.get("nome"),
                        escopo=tool_data.get("escopo"),
                    )
                )

        # Normaliza contratantes
        raw_contratantes = doc.get("contratantes") or []
        contratantes: List[str] = []
        print(raw_contratantes)
        if isinstance(raw_contratantes, str):
            try:
                raw_contratantes = json.loads(raw_contratantes)
            except Exception:
                raw_contratantes = []

        if isinstance(raw_contratantes, list):
            for c in raw_contratantes:
                if isinstance(c, list):  # flatten lista de listas
                    for item in c:
                        if item:
                            contratantes.append(str(item))
                elif c:
                    contratantes.append(str(c))

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            descricao=doc.get("descricao"),
            system_message=doc.get("system_message"),
            visivel=doc.get("visivel"),
            id_contratante=doc.get("id_contratante"),
            ativo=doc.get("ativo"),
            funcoes=doc.get("funcoes"),
            tools=tools,
            contratantes=contratantes,
        )
