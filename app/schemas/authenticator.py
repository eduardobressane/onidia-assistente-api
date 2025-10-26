from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, RootModel


# ======== MODELOS INTERNOS (EM CAMADAS) ========

class HeaderModel(BaseModel):
    name: str
    value: str


class AuthenticatorBody(RootModel[Dict[str, Any]]):
    """
    Representa o corpo da requisição do authenticator.
    Exemplo:
    {
        "client_id": "meu_id",
        "client_secret": "minha_senha"
    }
    """
    root: Dict[str, Any] = Field(default_factory=dict)


class ResponseMapModel(BaseModel):
    """
    Mapeia os campos que devem ser extraídos da resposta da autenticação.
    Exemplo:
    {
        "access_token": "$response.access_token",
        "expires_in": "$response.expires_in"
    }
    """
    access_token: Optional[str] = None
    expires_in: Optional[str] = None

    @field_validator("*", mode="before")
    @classmethod
    def ensure_str(cls, v):
        if v is None:
            return None
        if not isinstance(v, str):
            raise ValueError("Os valores do response_map devem ser strings")
        return v


# ======== MODELOS BASE ========

class AuthenticatorBase(BaseModel):
    name: str = Field(..., max_length=150)
    url: str
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)
    headers: List[HeaderModel] = Field(default_factory=list)
    response_map: Optional[ResponseMapModel] = None
    enabled: bool = Field(default=True)

    @field_validator("body", mode="before")
    @classmethod
    def ensure_body_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("body deve ser um dicionário")
        return v

    @field_validator("headers", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if not isinstance(v, list):
            raise ValueError("headers deve ser uma lista")
        return v


# ======== CREATE / UPDATE ========

class AuthenticatorCreate(AuthenticatorBase):
    pass


class AuthenticatorUpdate(AuthenticatorBase):
    pass


# ======== OUTPUT LIST ========

class AuthenticatorOutList(BaseModel):
    id: str
    name: str
    url: str
    method: str
    enabled: bool = True

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AuthenticatorOutList"]:
        if not doc:
            return None
        return cls(
            id=str(doc.get("_id")),
            name=doc.get("name"),
            url=doc.get("url"),
            method=doc.get("method"),
            enabled=doc.get("enabled", True)
        )


# ======== OUTPUT DETAIL ========

class AuthenticatorOutDetail(AuthenticatorBase):
    id: str

    @classmethod
    def from_raw(cls, doc: dict) -> Optional["AuthenticatorOutDetail"]:
        if not doc:
            return None

        import copy
        data = copy.deepcopy(doc)

        # Oculta segredos sensíveis no body (ex: client_secret)
        try:
            if "body" in data and isinstance(data["body"], dict):
                masked_body = {}
                for k, v in data["body"].items():
                    masked_body[k] = "****" if "secret" in k.lower() or "token" in k.lower() else v
                data["body"] = masked_body
        except Exception:
            pass

        return cls(
            id=str(data.get("_id")),
            name=data.get("name"),
            url=data.get("url"),
            method=data.get("method"),
            body=data.get("body", {}),
            headers=data.get("headers", []),
            response_map=data.get("response_map"),
            enabled=data.get("enabled", True),
        )
