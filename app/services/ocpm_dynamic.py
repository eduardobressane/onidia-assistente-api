from datetime import datetime
from bson import ObjectId
from uuid import UUID
from app.dataprovider.mongo.models.ocpm import collection as ocpm_coll
from app.dataprovider.mongo.models.service import collection as service_coll
from app.services.service import ServiceService
from app.core.exceptions.types import NotFoundError


class OCPMDynamicService:
    """
    Serviço dinâmico que gera endpoints MCP em tempo de execução.
    - registry() → lista todos os OCP-M disponíveis
    - schema() → retorna o schema OpenAPI-like
    - get_ocpm() → retorna o formato FastMCP
    - list_tools() → lista tools do OCP-M
    - execute_tool() → executa um service vinculado
    """

    @staticmethod
    def registry(contractor_id: UUID) -> list:
        """Lista todos os OCP-Ms disponíveis para auto-registro"""
        filtro = {"contractor_id": str(contractor_id)}
        ocpms = list(ocpm_coll.find(filtro, {"_id": 1, "name": 1, "description": 1}))

        registry = [
            {
                "id": str(o["_id"]),
                "name": o.get("name"),
                "description": o.get("description"),
                "url": f"/ocp-m/{str(o['_id'])}",
                "schema_url": f"/ocp-m/{str(o['_id'])}/schema.json",
                "tools_url": f"/ocp-m/{str(o['_id'])}/tools",
                "registered_at": datetime.now().isoformat()
            }
            for o in ocpms
        ]
        return registry

    # ==========================================================
    @staticmethod
    def schema(id: str) -> dict:
        """Retorna schema OpenAPI-like do OCP-M"""
        ocpm = ocpm_coll.find_one({"_id": ObjectId(id)})
        if not ocpm:
            raise NotFoundError(f"OCP-M com id={id} não encontrado")

        tools_metadata = []
        for t in ocpm.get("tools", []):
            service_id = t["service"]["id"]
            service_doc = service_coll.find_one({"_id": ObjectId(service_id)}, {"input_schema": 1, "method": 1, "url": 1})

            if not service_doc:
                continue

            tools_metadata.append({
                "name": t["name"],
                "description": t.get("description"),
                "method": service_doc.get("method", "GET"),
                "service_url": service_doc.get("url"),
                "execute_url": f"/ocp-m/{id}/tools/{t['name']}/execute",
                "input_schema": service_doc.get("input_schema"),
            })

        return {
            "ocp_m_id": str(ocpm["_id"]),
            "name": ocpm.get("name"),
            "description": ocpm.get("description"),
            "base_url": f"/ocp-m/{id}",
            "tools": tools_metadata,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0.0-ocpm"
            }
        }

    # ==========================================================
    @staticmethod
    def list_tools(id: str) -> dict:
        """Retorna formato padrão FastMCP"""
        ocpm = ocpm_coll.find_one({"_id": ObjectId(id)})
        if not ocpm:
            raise NotFoundError(f"OCP-M com id={id} não encontrado")

        return {
            "id": str(ocpm["_id"]),
            "name": ocpm.get("name"),
            "description": ocpm.get("description"),
            "tools": [
                {
                    "name": t["name"],
                    "description": t.get("description"),
                    "args": OCPMDynamicService._get_tool_schema(t["service"]["id"])
                }
                for t in ocpm.get("tools", [])
            ]
        }

    # ==========================================================
    @staticmethod
    def execute_tool(id: str, tool_name: str, inputs: dict | None = None) -> dict:
        """Executa a tool (chama ServiceService.execute)"""
        ocpm = ocpm_coll.find_one({"_id": ObjectId(id)})
        if not ocpm:
            raise NotFoundError(f"OCP-M com id={id} não encontrado")

        tool = next((t for t in ocpm.get("tools", []) if t["name"] == tool_name), None)
        if not tool:
            raise NotFoundError(f"Tool {tool_name} não encontrada neste OCP-M")

        service_id = tool["service"]["id"]
        return ServiceService.execute(service_id, inputs)

    # ==========================================================
    @staticmethod
    def _get_tool_schema(service_id: str) -> dict:
        """Obtém o input_schema do service"""
        doc = service_coll.find_one({"_id": ObjectId(service_id)})
        return doc.get("input_schema", {}) if doc else {}
