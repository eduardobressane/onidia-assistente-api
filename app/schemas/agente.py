from typing import List, Optional
from pydantic import BaseModel, Field, model_validator, field_validator
from app.core.exceptions.types import NotFoundError, BadRequestError
from bson import ObjectId

class Funcao(BaseModel):
    codigo: str = Field(..., max_length=10)
    nome: str = Field(..., max_length=150)
    system_message: str


class ToolInfo(BaseModel):
    id: str
    nome: str


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


class Tool(BaseModel):
    tool: ToolInfo
    nome: str


class AgenteBase(BaseModel):
    nome: str = Field(..., title="Nome do Agente", max_length=150)
    system_message: str = Field(..., title="System Message")
    visivel: bool = Field(default=True)
    publico: bool = Field(default=True)
    ativo: bool = Field(default=True)
    id_contratante: Optional[str] = None
    funcoes: Optional[List[Funcao]] = None

    @model_validator(mode="after")
    def validate_funcoes_unique(self):
        funcoes = self.funcoes or []
        codigos = [f.codigo for f in funcoes]
        if len(codigos) != len(set(codigos)):
            raise BadRequestError("Os códigos das funções devem ser únicos dentro do agente.") 
        return self


class AgenteCreate(AgenteBase):
    tools: List[ToolCreateOrUpdate]

    @model_validator(mode="after")
    def validate_tools_unique(self):
        nomes = [t.nome for t in self.tools or []]
        if len(nomes) != len(set(nomes)):
            raise BadRequestError("Os nomes das tools devem ser únicos dentro do agente.")
        return self


class AgenteUpdate(AgenteBase):
    tools: List[ToolCreateOrUpdate]

    @model_validator(mode="after")
    def validate_tools_unique(self):
        nomes = [t.nome for t in self.tools or []]
        if len(nomes) != len(set(nomes)):
            raise BadRequestError("Os nomes das tools devem ser únicos dentro do agente.")
        return self


class AgenteOutList(BaseModel):
    id: str
    nome: str
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
            # Se vier "tool_id", cria ToolInfo só com id
            if "tool_id" in t:
                tools.append(
                    Tool(
                        tool=ToolInfo(id=str(t["tool_id"]), nome=""),  # nome vazio (ou buscar depois)
                        nome=t.get("nome"),
                        escopo=t.get("escopo")
                    )
                )
            # Se vier "tool" já expandido
            elif "tool" in t:
                tool_data = t["tool"]
                tools.append(
                    Tool(
                        tool=ToolInfo(
                            id=str(tool_data.get("id")),
                            nome=tool_data.get("nome", "")
                        ),
                        nome=t.get("nome"),
                        escopo=t.get("escopo")
                    )
                )

        return cls(
            id=str(doc["_id"]),
            nome=doc.get("nome"),
            system_message=doc.get("system_message"),
            visivel=doc.get("visivel"),
            ativo=doc.get("ativo"),
            id_contratante=doc.get("id_contratante"),
            funcoes=doc.get("funcoes"),
            tools=tools,
        )
