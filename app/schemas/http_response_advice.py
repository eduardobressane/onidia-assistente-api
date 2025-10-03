from typing import Optional, Dict
from fastapi import status as http_status

from .http_response import HttpResponse, T


def ok(
    data: Optional[T] = None,
    message: Optional[str] = None,
    total: Optional[int] = None,
    pages: Optional[int] = None,
    status_code: int = http_status.HTTP_200_OK,
) -> HttpResponse[T]:
    return HttpResponse[T](
        message=message,
        status=status_code,
        success=True,
        total=total,
        pages=pages,
        data=data,
    )


def created(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> HttpResponse[T]:
    return HttpResponse[T](
        message=message or "Registro criado com sucesso!",
        status=http_status.HTTP_201_CREATED,
        success=True,
        data=data,
    )


def updated(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> HttpResponse[T]:
    return HttpResponse[T](
        message=message or "Registro atualizado com sucesso!",
        status=http_status.HTTP_200_OK,
        success=True,
        data=data,
    )


def deleted(
    data: Optional[T] = None,
    message: Optional[str] = None,
) -> HttpResponse[T]:
    return HttpResponse[T](
        message=message or "Registro excluído com sucesso!",
        status=http_status.HTTP_200_OK,
        success=True,
        data=data,
    )


def error(
    message: str,
    status_code: int = http_status.HTTP_400_BAD_REQUEST,
    errors: Optional[Dict[str, str]] = None,
) -> HttpResponse[None]:
    return HttpResponse[None](
        message=message,
        status=status_code,
        success=False,
        errors=errors,
    )


def negado() -> HttpResponse[None]:
    return HttpResponse[None](
        message="Acesso negado",
        status=http_status.HTTP_403_FORBIDDEN,
        success=False,
    )
