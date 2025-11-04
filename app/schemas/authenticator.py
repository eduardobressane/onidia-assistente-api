from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# ======== MODELOS BASE ========

class AuthenticatorBase(BaseModel):
    name: str = Field(..., max_length=150)
    url: str
    method: str = Field(..., pattern="^(GET|POST|PUT|DELETE|PATCH)$")
    body: Optional[Dict[str, Any]] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)
    response_map: Dict[str, Any] = Field(default_factory=dict)
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
    def ensure_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("headers deve ser um dicionário")
        return v

    @field_validator("response_map", mode="before")
    @classmethod
    def ensure_dict(cls, v):
        if v in (None, []):
            return {}
        if not isinstance(v, dict):
            raise ValueError("reponse map deve ser um dicionário")
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

        # Oculta valores sensíveis do body
        try:
            if isinstance(data.get("body"), dict):
                data["body"] = {k: "****" for k in data["body"].keys()}
        except Exception:
            pass

        # Oculta valores sensíveis dos headers
        try:
            if isinstance(data.get("headers"), dict):
                data["headers"] = {k: "****" for k in data["headers"].keys()}
        except Exception:
            pass

        return cls(
            id=str(data.get("_id")),
            name=data.get("name"),
            url=data.get("url"),
            method=data.get("method"),
            body=data.get("body", {}),
            headers=data.get("headers", {}),
            response_map=data.get("response_map", {}),
            enabled=data.get("enabled", True),
        )
