from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class SourceModel(BaseModel):
    id: Optional[str] = None
    type: Literal["mcp", "langserve"]  # <== restrição aqui
    url: str
    headers: List[Dict[str, Any]] | List[str] = Field(default_factory=list)


class MetadataModel(BaseModel):
    protocol: str
    version: str
    source: SourceModel


class ToolInputSchema(BaseModel):
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    additionalProperties: Optional[bool] = None


class ToolModel(BaseModel):
    name: str
    description: str = ""
    input_schema: ToolInputSchema


class StructureModel(BaseModel):
    description: str = ""
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    tools: List[ToolModel] = Field(default_factory=list)


class OCPModel(BaseModel):
    id: Optional[str] = None
    metadata: MetadataModel
    structure: StructureModel
