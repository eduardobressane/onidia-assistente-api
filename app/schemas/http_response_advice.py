from typing import Optional, TypeVar, Any, Dict
from fastapi import status as http_status
from starlette.responses import JSONResponse
from pydantic import BaseModel

from .http_response import HttpResponse, T  # assumindo que HttpResponse[T] é um BaseModel genérico

T = TypeVar("T")


# 🔧 Helper recursivo: mantém `null` dentro de `data`
def _dump_with_nulls(obj: Any):
    if isinstance(obj, BaseModel):
        return obj.model_dump(exclude_none=False)
    if isinstance(obj, list):
        return [_dump_with_nulls(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _dump_with_nulls(v) for k, v in obj.items()}
    return obj


# 🔧 Helper genérico para montar resposta padronizada
def _build_response(
    data: Optional[T],
    message: Optional[str],
    status_code: int,
    success: bool = True,
    total: Optional[int] = None,
    pages: Optional[int] = None,
    errors: Optional[Dict[str, str]] = None
) -> JSONResponse:
    response_model = HttpResponse[T](
        message=message,
        status=status_code,
        success=success,
        total=total,
        pages=pages,
        errors=errors,
        data=data,
    )

    # Oculta None no topo, mas mantém `data` com nulls
    content = response_model.model_dump(exclude_none=True)
    content["data"] = _dump_with_nulls(data)

    return JSONResponse(status_code=status_code, content=content)


# ✅ OK (consulta/listagem)
def ok(
    data: Optional[T] = None,
    message: Optional[str] = None,
    total: Optional[int] = None,
    pages: Optional[int] = None,
    status_code: int = http_status.HTTP_200_OK,
) -> JSONResponse:
    return _build_response(data, message, status_code, True, total, pages)


# ✅ Created
def created(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    return _build_response(
        data,
        message or "Registro criado com sucesso!",
        http_status.HTTP_200_OK
    )


# ✅ Updated
def updated(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    return _build_response(
        data,
        message or "Registro atualizado com sucesso!",
        http_status.HTTP_200_OK
    )


# ✅ Deleted
def deleted(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    return _build_response(
        data,
        message or "Registro excluído com sucesso!",
        http_status.HTTP_200_OK
    )


# ✅ Error genérico
def error(
    message: str,
    status_code: int = http_status.HTTP_400_BAD_REQUEST,
    errors: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    return _build_response(
        data=None,
        message=message,
        status_code=status_code,
        success=False,
        errors=errors
    )


# ✅ Acesso negado
def negado() -> JSONResponse:
    return _build_response(
        data=None,
        message="Acesso negado",
        status_code=http_status.HTTP_403_FORBIDDEN,
        success=False
    )
