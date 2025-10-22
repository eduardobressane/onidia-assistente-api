from typing import Generic, Optional, Sequence, TypeVar, Dict
from fastapi import status as http_status
from fastapi.responses import JSONResponse

from .http_response import HttpResponse, T

def ok(
    data: Optional[T] = None,
    message: Optional[str] = None,
    total: Optional[int] = None,
    pages: Optional[int] = None,
    status_code: int = http_status.HTTP_200_OK,
) -> JSONResponse:
    content = HttpResponse[T](
        message=message,
        status=status_code,
        success=True,
        total=total,
        pages=pages,
        data=data,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=status_code,
        content=content
    )

def created(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    content = HttpResponse[T](
        message=message or "Registro criado com sucesso!",
        status=http_status.HTTP_200_OK,
        success=True,
        data=data,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content=content
    )

def updated(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    content = HttpResponse[T](
        message=message or "Registro atualizado com sucesso!",
        status=http_status.HTTP_200_OK,
        success=True,
        data=data,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content=content
    )

def deleted(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> JSONResponse:
    content = HttpResponse[T](
        message=message or "Registro excluído com sucesso!",
        status=http_status.HTTP_200_OK,
        success=True,
        data=data,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=http_status.HTTP_200_OK,
        content=content
    )

def error(
    message: str,
    status_code: int = http_status.HTTP_400_BAD_REQUEST,
    errors: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    content = HttpResponse[None](
        message=message,
        status=status_code,
        success=False,
        errors=errors,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=status_code,
        content=content
    )

def negado() -> JSONResponse:
    content = HttpResponse[None](
        message="Acesso negado",
        status=403,
        success=False,
    ).model_dump(exclude_none=True)

    return JSONResponse(
        status_code=403,
        content=content
    )
