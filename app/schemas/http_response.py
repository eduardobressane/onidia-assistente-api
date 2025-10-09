from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Generic, Optional, TypeVar
from pydantic import ConfigDict, Field, field_serializer
from pydantic.generics import GenericModel
from bson import ObjectId

T = TypeVar("T")


class HttpResponse(GenericModel, Generic[T]):
    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
        ser_json_exclude_none=True,
        json_encoders={ObjectId: str},
    )

    message: Optional[str] = None
    status: int = Field(..., description="HTTP status code")
    success: bool = Field(..., description="Operation succeeded?")
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total: Optional[int] = None
    pages: Optional[int] = None
    data: Optional[T] = None
    errors: Optional[Dict[str, str]] = None

    @field_serializer("date")
    def serialize_date(self, dt: datetime, _info):
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
