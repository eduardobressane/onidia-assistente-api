from fastapi import APIRouter, Path, Body, Depends, Query
from app.services.ocpm_dynamic import OCPMDynamicService
from app.schemas.http_response import HttpResponse
from app.schemas.http_response_advice import ok, error
from app.core.security import require_permissions, get_current_user, validate_and_alter_contractor
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/ocp-m/dynamic", tags=["OCP-M Dynamic"])


@router.get(
    "/registry",
    response_model=HttpResponse[list],
    dependencies=[Depends(require_permissions(["*", "hcopm_registry"]))],
)
def registry(
    contractor_id: Optional[UUID] = Query(None),
    current_user: dict = Depends(get_current_user),
    ):
    """Lista todos os OCP-Ms disponíveis para auto-registro."""
    contractor_id = validate_and_alter_contractor(current_user, contractor_id)
    
    try:
        return ok(data=OCPMDynamicService.registry(contractor_id))
    except Exception as e:
        return error(status_code=400, message=f"Erro ao listar OCP-Ms: {str(e)}")


@router.get(
    "/{id}/schema.json",
    response_model=HttpResponse[dict],
    dependencies=[Depends(require_permissions(["*", "hcopm_view"]))],
)
def get_schema(id: str = Path(...)):
    """Retorna metadados OpenAPI-like do OCP-M"""
    try:
        return ok(data=OCPMDynamicService.schema(id))
    except Exception as e:
        return error(status_code=400, message=f"Erro ao montar schema OCP-M: {str(e)}")


@router.get(
    "/{id}/tools",
    response_model=HttpResponse[dict]
)
def list_tools(id: str = Path(...)):
    """Retorna o formato FastMCP completo"""
    try:
        return ok(data=OCPMDynamicService.list_tools(id))
    except Exception as e:
        return error(status_code=400, message=f"Erro ao montar OCP-M: {str(e)}")


@router.post(
    "/{id}/tools/{tool_name}/execute",
    response_model=HttpResponse[dict],
    dependencies=[Depends(require_permissions(["*", "hcopm_execute"]))],
)
def execute_tool(id: str = Path(...), tool_name: str = Path(...), inputs: dict = Body(None)):
    """Executa uma tool vinculada ao OCP-M"""
    try:
        result = OCPMDynamicService.execute_tool(id, tool_name, inputs)
        return ok(data=result)
    except Exception as e:
        return error(status_code=400, message=f"Erro ao executar tool {tool_name}: {str(e)}")
