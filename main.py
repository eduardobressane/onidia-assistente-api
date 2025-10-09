from dotenv import load_dotenv
import os

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.core.exceptions.types import DomainError
from app.core.exceptions.handlers import (
    domain_error_handler,
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)

from app.controllers import auth
from app.controllers import modelo_ai as modelo_ai_ctrl
from app.controllers import tool as tool_ctrl
from app.controllers import credencial_tool as credencial_tool_ctrl
from app.core.translations import TRANSLATIONS

# --- Carregar variáveis ---
load_dotenv()
app_name = os.getenv("APP_NAME")

app = FastAPI(title=app_name)

# --- Exception Handlers (ordem explícita ajuda na leitura) ---
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# --- Rotas ---
app.include_router(auth.router)
app.include_router(modelo_ai_ctrl.router)
app.include_router(tool_ctrl.router)
app.include_router(credencial_tool_ctrl.router)