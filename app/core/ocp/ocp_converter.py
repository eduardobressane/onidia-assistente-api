from typing import Dict, List, Optional


# =========================
# Funções privadas - versão 1.0.0
# =========================

# ocp_converter.py (trecho atualizado)

def _mcp_to_ocp_v1(mcp_obj: Dict, url: str = "", headers: Optional[List] = None) -> Dict:
    return {
        "metadata": {
            "protocol": "OCP",
            "version": "1.0.0",
            "source": {
                "id": mcp_obj.get("id"),
                "type": "mcp",
                "url": url,
                "headers": headers or []
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
                        tool.get("input_schema")  # já vem pronto no MCP
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

def _langserve_to_ocp_v1(ls_obj: Dict, url: str = "", headers: Optional[List] = None) -> Dict:
    return {
        "metadata": {
            "protocol": "OCP",
            "version": "1.0.0",
            "source": {
                "id": ls_obj.get("id"),
                "type": "langserve",
                "url": url,
                "headers": headers or []
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
# Métodos públicos - escolhem a versão
# =========================

def mcp_to_ocp(mcp_obj: Dict, url: str = "", headers: Optional[List] = None, version: str = "1.0.0") -> Dict:
    """Converte um objeto MCP para OCP na versão especificada."""
    if version == "1.0.0":
        return _mcp_to_ocp_v1(mcp_obj, url, headers)
    else:
        raise ValueError(f"Versão MCP->OCP não suportada: {version}")


def langserve_to_ocp(ls_obj: Dict, url: str = "", headers: Optional[List] = None, version: str = "1.0.0") -> Dict:
    """Converte um objeto LangServe para OCP na versão especificada."""
    if version == "1.0.0":
        return _langserve_to_ocp_v1(ls_obj, url, headers)
    else:
        raise ValueError(f"Versão LangServe->OCP não suportada: {version}")
