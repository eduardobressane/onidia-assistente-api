from typing import Dict, List, Optional, Literal, Any
from app.core.exceptions.types import BadRequestError

class OCPConverter:

    # =========================
    # Private functions - version 1.0.0
    # =========================

    @staticmethod
    def _mcp_to_ocp_v1_0_0(mcp_obj: Dict, url: str = "", headers: Optional[List] = None) -> Dict:
        return {
            "metadata": {
                "protocol": "OCP",
                "version": "1.0.0",
                "source": {
                    "id": mcp_obj.get("id"),
                    "type": "mcp",
                    "url": url,
                    "headers": headers or {}
                }
            },
            "structure": {
                "description": mcp_obj.get("metadata", {}).get("description", ""),
                "input_schema": mcp_obj.get("input_schema", {}),
                "output_schema": mcp_obj.get("output_schema", {}),
                "tools": [
                    {
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "input_schema": (
                            tool.get("input_schema")
                            or {
                                "type": "object",
                                "properties": tool.get("args", {}),
                                "required": list(tool.get("args", {}).keys())
                            }
                        )
                    }
                    for tool in mcp_obj.get("tools", [])
                ]
            }
        }

    @staticmethod
    def _langserve_to_ocp_v1_0_0(ls_obj: Dict, url: str = "", headers: Optional[List] = None) -> Dict:
        return {
            "metadata": {
                "protocol": "OCP",
                "version": "1.0.0",
                "source": {
                    "id": ls_obj.get("id"),
                    "type": "langserve",
                    "url": url,
                    "headers": headers or {}
                }
            },
            "structure": {
                "description": ls_obj.get("metadata", {}).get("description", ""),
                "input_schema": ls_obj.get("input_schema", {}),
                "output_schema": ls_obj.get("output_schema", {}),
                "tools": [
                    {
                        "name": tool.get("name"),
                        "description": tool.get("description", ""),
                        "input_schema": {
                            "type": "object",
                            "properties": tool.get("args", {}),
                            "required": list(tool.get("args", {}).keys())
                        }
                    }
                    for tool in ls_obj.get("tools", [])
                ]
            }
        }


    # =========================
    # Public methods - choose version
    # =========================
    def ocp(ocpType: Literal["mcp", "langserve"], obj: Dict, url: str = "", headers: Optional[Dict[str, Any]] = None, version: str = "1.0.0"):
        if "mcp" in ocpType:
            return OCPConverter.mcp_to_ocp(mcp_obj=obj, url=url, headers=headers, version=version)
        else:
            return OCPConverter.langserve_to_ocp(ls_obj=obj, url=url, headers=headers, version=version)

    @staticmethod
    def mcp_to_ocp(mcp_obj: Dict, url: str = "", headers: Optional[List] = None, version: str = "1.0.0") -> Dict:
        """Converte um objeto MCP para OCP na versão especificada."""

        url = url.strip()
        if url.endswith("/tools"):
            url = url[:-6].strip()

        if version == "1.0.0":
            return OCPConverter._mcp_to_ocp_v1_0_0(mcp_obj, url, headers)
        else:
            raise BadRequestError(f"Versão MCP->OCP não suportada: {version}")


    @staticmethod
    def langserve_to_ocp(ls_obj: Dict, url: str = "", headers: Optional[List] = None, version: str = "1.0.0") -> Dict:
        """Converte um objeto LangServe para OCP na versão especificada."""
        if version == "1.0.0":
            return OCPConverter._langserve_to_ocp_v1_0_0(ls_obj, url, headers)
        else:
            raise BadRequestError(f"Versão LangServe->OCP não suportada: {version}")
