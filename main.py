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
from app.controllers import assistant as assistant_ctrl
from app.controllers import agent as agent_ctrl
from app.controllers import credential_type as credential_type_ctrl
from app.controllers import credential as credential_ctrl
from app.controllers import tag as tag_ctrl
from app.controllers import ocp as ocp_ctrl
from app.controllers import authenticator as authenticator_ctrl
from app.controllers import service as service_ctrl
from app.controllers import ocpm as ocpm_ctrl

from app.core.translations import TRANSLATIONS

# --- Load variables ---
load_dotenv()
app_name = os.getenv("APP_NAME")

app = FastAPI(title=app_name)

# --- Exception Handlers (ordem explícita ajuda na leitura) ---
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# --- Routers ---
app.include_router(auth.router)
app.include_router(assistant_ctrl.router)
app.include_router(agent_ctrl.router)
app.include_router(credential_type_ctrl.router)
app.include_router(credential_ctrl.router)
app.include_router(tag_ctrl.router)
app.include_router(ocp_ctrl.router)
app.include_router(authenticator_ctrl.router)
app.include_router(service_ctrl.router)
app.include_router(ocpm_ctrl.router)