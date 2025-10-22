from fastapi import Request, HTTPException
from fastapi.exceptions import RequestValidationError
from typing import Dict, List

from app.schemas.http_response_advice import error
from .types import DomainError

from fastapi.responses import JSONResponse
from app.core.translations import TRANSLATIONS

async def domain_error_handler(request: Request, exc: DomainError):
    # exc.status_code vem do DomainError (404, 409, etc.)
    return error(message=str(exc.detail), status_code=exc.status_code)

async def http_exception_handler(request: Request, exc: HTTPException):
    # Converte HTTPException nativa pro mesmo contrato
    # útil se algum endpoint ainda fizer raise HTTPException
    return error(message=str(exc.detail), status_code=exc.status_code)

def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Traduz mensagens de validação.
    Monta dict campo->mensagem (sem prefixo 'body').
    """
    field_errors: Dict[str, str] = {}

    for err in exc.errors():
        # Remove sempre "body" do caminho
        loc = [str(l) for l in err.get("loc", []) if l != "body"]
        path = ".".join(loc) if loc else "body"

        msg = err.get("msg", "Inválido")

        # aplica tradução se houver
        for en, pt in TRANSLATIONS.items():
            if msg.startswith(en) or msg == en:
                msg = msg.replace(en, pt)
                break

        field_errors[path] = msg

    return error(
        message="Erro de validação",
        status_code=422,
        errors=field_errors
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    # fallback pra qualquer coisa não mapeada
    return error(message="Erro interno do servidor", status_code=500)